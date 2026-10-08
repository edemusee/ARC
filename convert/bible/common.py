"""Shared tables and helpers for the Bible / Enoch / Jubilees converters.

Run the converters with `python3 -I convert/bible/<script>.py` from the reader root; every script
adds its own directory to sys.path so this module can be imported under -I.
"""
import json
import os
import re
import unicodedata

READER_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WORKS = os.path.join(READER_ROOT, 'works')

# ---------------------------------------------------------------- book codes

OT39 = ['gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jdg', 'rut', '1sa', '2sa', '1ki', '2ki', '1ch', '2ch',
        'ezr', 'neh', 'est', 'job', 'psa', 'pro', 'ecc', 'sng', 'isa', 'jer', 'lam', 'ezk', 'dan', 'hos',
        'jol', 'amo', 'oba', 'jon', 'mic', 'nam', 'hab', 'zep', 'hag', 'zec', 'mal']
NT27 = ['mat', 'mrk', 'luk', 'jhn', 'act', 'rom', '1co', '2co', 'gal', 'eph', 'php', 'col', '1th', '2th',
        '1ti', '2ti', 'tit', 'phm', 'heb', 'jas', '1pe', '2pe', '1jn', '2jn', '3jn', 'jud', 'rev']

CANONS = {
    'protestant-66': OT39 + NT27,
    'catholic-73': ['gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jdg', 'rut', '1sa', '2sa', '1ki', '2ki', '1ch', '2ch',
                    'ezr', 'neh', 'tob', 'jdt', 'est', '1ma', '2ma', 'job', 'psa', 'pro', 'ecc', 'sng', 'wis', 'sir',
                    'isa', 'jer', 'lam', 'bar', 'ezk', 'dan', 'hos', 'jol', 'amo', 'oba', 'jon', 'mic', 'nam', 'hab',
                    'zep', 'hag', 'zec', 'mal'] + NT27,
    'kjv-apocrypha-80': OT39 + ['1es', '2es', 'tob', 'jdt', 'esg', 'wis', 'sir', 'bar', 'pra', 'sus', 'bel', 'man',
                                '1ma', '2ma'] + NT27,
    'orthodox-web-84': OT39 + ['tob', 'jdt', 'esg', 'wis', 'sir', 'bar', 'lje', 'pra', 'sus', 'bel', '1ma', '2ma',
                               '1es', 'man', 'ps151', '3ma', '2es', '4ma'] + NT27,
    # Brenton: KJV order (as the FreeBiblos file is indexed), Psalm 151 after the Psalms, extras after.
    'lxx-brenton': OT39[:OT39.index('psa') + 1] + ['ps151'] + OT39[OT39.index('psa') + 1:] +
                   ['1es', 'tob', 'jdt', '1ma', '2ma', '3ma', '4ma', 'wis', 'sir', 'man', 'bar', 'lje', 'sus', 'bel'],
}

BOOK_NAMES = {
    'gen': 'Genesis', 'exo': 'Exodus', 'lev': 'Leviticus', 'num': 'Numbers', 'deu': 'Deuteronomy',
    'jos': 'Joshua', 'jdg': 'Judges', 'rut': 'Ruth', '1sa': '1 Samuel', '2sa': '2 Samuel',
    '1ki': '1 Kings', '2ki': '2 Kings', '1ch': '1 Chronicles', '2ch': '2 Chronicles', 'ezr': 'Ezra',
    'neh': 'Nehemiah', 'tob': 'Tobit', 'jdt': 'Judith', 'est': 'Esther', '1ma': '1 Maccabees', '2ma': '2 Maccabees',
    'job': 'Job', 'psa': 'Psalms', 'pro': 'Proverbs', 'ecc': 'Ecclesiastes', 'sng': 'Song of Songs',
    'wis': 'Wisdom', 'sir': 'Sirach', 'isa': 'Isaiah', 'jer': 'Jeremiah', 'lam': 'Lamentations', 'bar': 'Baruch',
    'ezk': 'Ezekiel', 'dan': 'Daniel', 'hos': 'Hosea', 'jol': 'Joel', 'amo': 'Amos', 'oba': 'Obadiah',
    'jon': 'Jonah', 'mic': 'Micah', 'nam': 'Nahum', 'hab': 'Habakkuk', 'zep': 'Zephaniah', 'hag': 'Haggai',
    'zec': 'Zechariah', 'mal': 'Malachi',
    'mat': 'Matthew', 'mrk': 'Mark', 'luk': 'Luke', 'jhn': 'John', 'act': 'Acts', 'rom': 'Romans',
    '1co': '1 Corinthians', '2co': '2 Corinthians', 'gal': 'Galatians', 'eph': 'Ephesians', 'php': 'Philippians',
    'col': 'Colossians', '1th': '1 Thessalonians', '2th': '2 Thessalonians', '1ti': '1 Timothy', '2ti': '2 Timothy',
    'tit': 'Titus', 'phm': 'Philemon', 'heb': 'Hebrews', 'jas': 'James', '1pe': '1 Peter', '2pe': '2 Peter',
    '1jn': '1 John', '2jn': '2 John', '3jn': '3 John', 'jud': 'Jude', 'rev': 'Revelation',
    '1es': '1 Esdras', '2es': '2 Esdras', 'esg': 'Esther (Greek)', 'pra': 'Prayer of Azariah', 'sus': 'Susanna',
    'bel': 'Bel and the Dragon', 'man': 'Prayer of Manasseh', 'lje': 'Letter of Jeremiah', 'ps151': 'Psalm 151',
    '3ma': '3 Maccabees', '4ma': '4 Maccabees',
}

# scrollmapper JSON book names (KJVA / DRC / FreCrampon) -> code
SCROLLMAPPER_NAMES = {
    'Genesis': 'gen', 'Exodus': 'exo', 'Leviticus': 'lev', 'Numbers': 'num', 'Deuteronomy': 'deu', 'Joshua': 'jos',
    'Judges': 'jdg', 'Ruth': 'rut', 'I Samuel': '1sa', 'II Samuel': '2sa', 'I Kings': '1ki', 'II Kings': '2ki',
    'I Chronicles': '1ch', 'II Chronicles': '2ch', 'Ezra': 'ezr', 'Nehemiah': 'neh', 'Esther': 'est', 'Job': 'job',
    'Psalms': 'psa', 'Proverbs': 'pro', 'Ecclesiastes': 'ecc', 'Song of Solomon': 'sng', 'Isaiah': 'isa',
    'Jeremiah': 'jer', 'Lamentations': 'lam', 'Ezekiel': 'ezk', 'Daniel': 'dan', 'Hosea': 'hos', 'Joel': 'jol',
    'Amos': 'amo', 'Obadiah': 'oba', 'Jonah': 'jon', 'Micah': 'mic', 'Nahum': 'nam', 'Habakkuk': 'hab',
    'Zephaniah': 'zep', 'Haggai': 'hag', 'Zechariah': 'zec', 'Malachi': 'mal',
    'I Esdras': '1es', 'II Esdras': '2es', 'Tobit': 'tob', 'Judith': 'jdt', 'Additions to Esther': 'esg',
    'Wisdom': 'wis', 'Sirach': 'sir', 'Baruch': 'bar', 'Prayer of Azariah': 'pra', 'Susanna': 'sus',
    'Bel and the Dragon': 'bel', 'Prayer of Manasses': 'man', 'I Maccabees': '1ma', 'II Maccabees': '2ma',
    'Matthew': 'mat', 'Mark': 'mrk', 'Luke': 'luk', 'John': 'jhn', 'Acts': 'act', 'Romans': 'rom',
    'I Corinthians': '1co', 'II Corinthians': '2co', 'Galatians': 'gal', 'Ephesians': 'eph', 'Philippians': 'php',
    'Colossians': 'col', 'I Thessalonians': '1th', 'II Thessalonians': '2th', 'I Timothy': '1ti', 'II Timothy': '2ti',
    'Titus': 'tit', 'Philemon': 'phm', 'Hebrews': 'heb', 'James': 'jas', 'I Peter': '1pe', 'II Peter': '2pe',
    'I John': '1jn', 'II John': '2jn', 'III John': '3jn', 'Jude': 'jud', 'Revelation of John': 'rev',
}

# USFX / Paratext ids -> code (identity for most; the exceptions are spelled out)
USFX_IDS = {'S3Y': 'pra', 'PS2': 'ps151', 'ESG': 'esg', 'LJE': 'lje'}

def usfx_code(bid):
    if bid in USFX_IDS:
        return USFX_IDS[bid]
    code = bid.lower()
    return code if code in BOOK_NAMES else None

# OSIS ids -> code
OSIS_IDS = {
    'Gen': 'gen', 'Exod': 'exo', 'Lev': 'lev', 'Num': 'num', 'Deut': 'deu', 'Josh': 'jos', 'Judg': 'jdg', 'Ruth': 'rut',
    '1Sam': '1sa', '2Sam': '2sa', '1Kgs': '1ki', '2Kgs': '2ki', '1Chr': '1ch', '2Chr': '2ch', 'Ezra': 'ezr', 'Neh': 'neh',
    'Esth': 'est', 'Job': 'job', 'Ps': 'psa', 'Prov': 'pro', 'Eccl': 'ecc', 'Song': 'sng', 'Isa': 'isa', 'Jer': 'jer',
    'Lam': 'lam', 'Ezek': 'ezk', 'Dan': 'dan', 'Hos': 'hos', 'Joel': 'jol', 'Amos': 'amo', 'Obad': 'oba', 'Jonah': 'jon',
    'Mic': 'mic', 'Nah': 'nam', 'Hab': 'hab', 'Zeph': 'zep', 'Hag': 'hag', 'Zech': 'zec', 'Mal': 'mal',
    'Matt': 'mat', 'Mark': 'mrk', 'Luke': 'luk', 'John': 'jhn', 'Acts': 'act', 'Rom': 'rom', '1Cor': '1co', '2Cor': '2co',
    'Gal': 'gal', 'Eph': 'eph', 'Phil': 'php', 'Col': 'col', '1Thess': '1th', '2Thess': '2th', '1Tim': '1ti', '2Tim': '2ti',
    'Titus': 'tit', 'Phlm': 'phm', 'Heb': 'heb', 'Jas': 'jas', '1Pet': '1pe', '2Pet': '2pe', '1John': '1jn', '2John': '2jn',
    '3John': '3jn', 'Jude': 'jud', 'Rev': 'rev',
}

# ---------------------------------------------------------------- aliases
# Typed-reference names (English full names and abbreviations, plus Spanish, German, French and Latin
# names from the editions carried). Everything is lower-cased and NFC'd on output.

ALIASES = {
    'gen': ['Genesis', 'Gen', 'Ge', 'Gn', 'Génesis', 'Genesis', '1 Mose', '1. Mose', '1Mo', 'Genèse', 'Gn'],
    'exo': ['Exodus', 'Exo', 'Ex', 'Exod', 'Éxodo', 'Exodo', '2 Mose', '2. Mose', '2Mo', 'Exode'],
    'lev': ['Leviticus', 'Lev', 'Le', 'Lv', 'Levítico', 'Levitico', '3 Mose', '3. Mose', '3Mo', 'Lévitique', 'Levitique'],
    'num': ['Numbers', 'Num', 'Nu', 'Nm', 'Nb', 'Números', 'Numeros', '4 Mose', '4. Mose', '4Mo', 'Nombres', 'Numeri'],
    'deu': ['Deuteronomy', 'Deut', 'Deu', 'De', 'Dt', 'Deuteronomio', '5 Mose', '5. Mose', '5Mo', 'Deutéronome', 'Deuteronome', 'Deuteronomium'],
    'jos': ['Joshua', 'Josh', 'Jos', 'Jsh', 'Josué', 'Josue', 'Josua'],
    'jdg': ['Judges', 'Judg', 'Jdg', 'Jg', 'Jdgs', 'Jueces', 'Richter', 'Ri', 'Juges', 'Judices'],
    'rut': ['Ruth', 'Rut', 'Ru', 'Rt', 'Rth'],
    '1sa': ['1 Samuel', '1Samuel', '1 Sam', '1Sam', '1 Sa', '1Sa', '1 Sm', '1Sm', 'I Samuel', 'First Samuel', '1. Samuel'],
    '2sa': ['2 Samuel', '2Samuel', '2 Sam', '2Sam', '2 Sa', '2Sa', '2 Sm', '2Sm', 'II Samuel', 'Second Samuel', '2. Samuel'],
    '1ki': ['1 Kings', '1Kings', '1 Kgs', '1Kgs', '1 Ki', '1Ki', '1 Kg', 'I Kings', 'First Kings', '1 Reyes', '1Reyes', '1 Könige', '1. Könige', '1 Koenige', '1Kön', '1 Rois', '1Rois', '1 R', '3 Kings', 'III Kings', '3 Reyes'],
    '2ki': ['2 Kings', '2Kings', '2 Kgs', '2Kgs', '2 Ki', '2Ki', '2 Kg', 'II Kings', 'Second Kings', '2 Reyes', '2Reyes', '2 Könige', '2. Könige', '2 Koenige', '2Kön', '2 Rois', '2Rois', '2 R', '4 Kings', 'IV Kings', '4 Reyes'],
    '1ch': ['1 Chronicles', '1Chronicles', '1 Chr', '1Chr', '1 Ch', '1Ch', '1 Chron', 'I Chronicles', 'First Chronicles', '1 Crónicas', '1 Cronicas', '1Cr', '1 Chronik', '1. Chronik', '1Chr', '1 Chroniques', '1Chroniques', '1 Paralipomenon', '1 Paralipómenos'],
    '2ch': ['2 Chronicles', '2Chronicles', '2 Chr', '2Chr', '2 Ch', '2Ch', '2 Chron', 'II Chronicles', 'Second Chronicles', '2 Crónicas', '2 Cronicas', '2Cr', '2 Chronik', '2. Chronik', '2 Chroniques', '2Chroniques', '2 Paralipomenon', '2 Paralipómenos'],
    'ezr': ['Ezra', 'Ezr', 'Esdras', 'Esd', 'Esra'],
    'neh': ['Nehemiah', 'Neh', 'Ne', 'Nehemías', 'Nehemias', 'Nehemia', 'Néhémie', 'Nehemie'],
    'tob': ['Tobit', 'Tob', 'Tb', 'Tobias', 'Tobías', 'Tobie'],
    'jdt': ['Judith', 'Jdt', 'Jth', 'Jdth', 'Judit'],
    'est': ['Esther', 'Est', 'Es', 'Esth', 'Ester'],
    '1ma': ['1 Maccabees', '1Maccabees', '1 Mac', '1Mac', '1 Macc', '1Macc', '1 Ma', '1Ma', 'I Maccabees', 'First Maccabees', '1 Macabeos', '1 Makkabäer', '1 Makkabaeer', '1 Maccabées', '1 Maccabees', '1 Machabees', '1 Machabeorum'],
    '2ma': ['2 Maccabees', '2Maccabees', '2 Mac', '2Mac', '2 Macc', '2Macc', '2 Ma', '2Ma', 'II Maccabees', 'Second Maccabees', '2 Macabeos', '2 Makkabäer', '2 Makkabaeer', '2 Maccabées', '2 Machabees', '2 Machabeorum'],
    '3ma': ['3 Maccabees', '3Maccabees', '3 Mac', '3Mac', '3 Macc', '3Macc', '3 Ma', 'III Maccabees', 'Third Maccabees'],
    '4ma': ['4 Maccabees', '4Maccabees', '4 Mac', '4Mac', '4 Macc', '4Macc', '4 Ma', 'IV Maccabees', 'Fourth Maccabees'],
    'job': ['Job', 'Jb', 'Hiob', 'Iob'],
    'psa': ['Psalms', 'Psalm', 'Psa', 'Ps', 'Pss', 'Psm', 'Pslm', 'Psalter', 'Salmos', 'Salmo', 'Sal', 'Psalmen', 'Psaumes', 'Psaume', 'Psalmi'],
    'pro': ['Proverbs', 'Prov', 'Pro', 'Pr', 'Prv', 'Proverbios', 'Sprüche', 'Sprueche', 'Spr', 'Sprichwörter', 'Proverbes', 'Proverbia'],
    'ecc': ['Ecclesiastes', 'Eccl', 'Ecc', 'Ec', 'Eccles', 'Qoheleth', 'Qohelet', 'Koheleth', 'Eclesiastés', 'Eclesiastes', 'Prediger', 'Pred', 'Ecclésiaste', 'Ecclesiaste', 'Kohelet'],
    'sng': ['Song of Songs', 'Song of Solomon', 'Song', 'Sng', 'So', 'SoS', 'SS', 'Canticles', 'Cant', 'Canticle of Canticles', 'Cantares', 'Cantar de los Cantares', 'Hohelied', 'Hoheslied', 'Hld', 'Cantique des Cantiques', 'Cantique', 'Canticum Canticorum'],
    'wis': ['Wisdom', 'Wis', 'Ws', 'Wisdom of Solomon', 'Wisd', 'Sabiduría', 'Sabiduria', 'Weisheit', 'Sagesse', 'Sapientia'],
    'sir': ['Sirach', 'Sir', 'Ecclesiasticus', 'Ecclus', 'Eccli', 'Ben Sira', 'Eclesiástico', 'Eclesiastico', 'Jesus Sirach', 'Siracide', 'Ecclésiastique'],
    'isa': ['Isaiah', 'Isa', 'Is', 'Isaías', 'Isaias', 'Jesaja', 'Jes', 'Ésaïe', 'Esaïe', 'Esaie', 'Isaïe', 'Isaie'],
    'jer': ['Jeremiah', 'Jer', 'Je', 'Jr', 'Jeremías', 'Jeremias', 'Jeremia', 'Jérémie', 'Jeremie'],
    'lam': ['Lamentations', 'Lam', 'La', 'Lamentaciones', 'Klagelieder', 'Klgl', 'Lamentationes'],
    'bar': ['Baruch', 'Bar', 'Ba'],
    'ezk': ['Ezekiel', 'Ezek', 'Eze', 'Ezk', 'Ez', 'Ezequiel', 'Hesekiel', 'Hes', 'Ézéchiel', 'Ezéchiel', 'Ezechiel'],
    'dan': ['Daniel', 'Dan', 'Da', 'Dn'],
    'hos': ['Hosea', 'Hos', 'Ho', 'Oseas', 'Osée', 'Osee', 'Osea'],
    'jol': ['Joel', 'Jol', 'Joe', 'Jl', 'Joël'],
    'amo': ['Amos', 'Amo', 'Am', 'Amós'],
    'oba': ['Obadiah', 'Obad', 'Oba', 'Ob', 'Abdías', 'Abdias', 'Obadja', 'Abdia'],
    'jon': ['Jonah', 'Jon', 'Jnh', 'Jonás', 'Jonas', 'Jona'],
    'mic': ['Micah', 'Mic', 'Mi', 'Miqueas', 'Micha', 'Michée', 'Michee', 'Michaea'],
    'nam': ['Nahum', 'Nah', 'Nam', 'Na', 'Nahúm'],
    'hab': ['Habakkuk', 'Hab', 'Hb', 'Habacuc', 'Habakuk'],
    'zep': ['Zephaniah', 'Zeph', 'Zep', 'Zp', 'Sofonías', 'Sofonias', 'Zephanja', 'Zefanja', 'Sophonie', 'Sophonias'],
    'hag': ['Haggai', 'Hag', 'Hg', 'Hageo', 'Haggaï', 'Aggée', 'Aggee', 'Aggaeus'],
    'zec': ['Zechariah', 'Zech', 'Zec', 'Zc', 'Zacarías', 'Zacarias', 'Sacharja', 'Sach', 'Zacharie', 'Zacharias'],
    'mal': ['Malachi', 'Mal', 'Ml', 'Malaquías', 'Malaquias', 'Maleachi', 'Malachie', 'Malachias'],
    'mat': ['Matthew', 'Matt', 'Mat', 'Mt', 'Mateo', 'Matthäus', 'Matthaeus', 'Matthieu', 'Matthaeum'],
    'mrk': ['Mark', 'Mrk', 'Mk', 'Mr', 'Marcos', 'Markus', 'Marc', 'Marcum'],
    'luk': ['Luke', 'Luk', 'Lk', 'Lu', 'Lucas', 'Lukas', 'Luc', 'Lucam'],
    'jhn': ['John', 'Jhn', 'Jn', 'Joh', 'Juan', 'Johannes', 'Jean', 'Ioannem'],
    'act': ['Acts', 'Act', 'Ac', 'Acts of the Apostles', 'Hechos', 'Hch', 'Apostelgeschichte', 'Apg', 'Actes', 'Actus Apostolorum'],
    'rom': ['Romans', 'Rom', 'Ro', 'Rm', 'Romanos', 'Römer', 'Roemer', 'Röm', 'Romains', 'Romanos'],
    '1co': ['1 Corinthians', '1Corinthians', '1 Cor', '1Cor', '1 Co', '1Co', 'I Corinthians', 'First Corinthians', '1 Corintios', '1Corintios', '1 Korinther', '1. Korinther', '1Kor', '1 Corinthiens', '1Corinthiens'],
    '2co': ['2 Corinthians', '2Corinthians', '2 Cor', '2Cor', '2 Co', '2Co', 'II Corinthians', 'Second Corinthians', '2 Corintios', '2Corintios', '2 Korinther', '2. Korinther', '2Kor', '2 Corinthiens', '2Corinthiens'],
    'gal': ['Galatians', 'Gal', 'Ga', 'Gálatas', 'Galatas', 'Galater', 'Galates'],
    'eph': ['Ephesians', 'Eph', 'Ep', 'Efesios', 'Epheser', 'Éphésiens', 'Ephesiens', 'Ephésiens'],
    'php': ['Philippians', 'Phil', 'Php', 'Pp', 'Filipenses', 'Philipper', 'Philippiens'],
    'col': ['Colossians', 'Col', 'Co', 'Colosenses', 'Kolosser', 'Kol', 'Colossiens'],
    '1th': ['1 Thessalonians', '1Thessalonians', '1 Thess', '1Thess', '1 Th', '1Th', '1 Thes', 'I Thessalonians', 'First Thessalonians', '1 Tesalonicenses', '1Tesalonicenses', '1 Thessalonicher', '1. Thessalonicher', '1Thess', '1 Thessaloniciens', '1Thessaloniciens'],
    '2th': ['2 Thessalonians', '2Thessalonians', '2 Thess', '2Thess', '2 Th', '2Th', '2 Thes', 'II Thessalonians', 'Second Thessalonians', '2 Tesalonicenses', '2Tesalonicenses', '2 Thessalonicher', '2. Thessalonicher', '2 Thessaloniciens', '2Thessaloniciens'],
    '1ti': ['1 Timothy', '1Timothy', '1 Tim', '1Tim', '1 Ti', '1Ti', 'I Timothy', 'First Timothy', '1 Timoteo', '1Timoteo', '1 Timotheus', '1. Timotheus', '1 Timothée', '1Timothée', '1 Timothee'],
    '2ti': ['2 Timothy', '2Timothy', '2 Tim', '2Tim', '2 Ti', '2Ti', 'II Timothy', 'Second Timothy', '2 Timoteo', '2Timoteo', '2 Timotheus', '2. Timotheus', '2 Timothée', '2Timothée', '2 Timothee'],
    'tit': ['Titus', 'Tit', 'Ti', 'Tito', 'Tite'],
    'phm': ['Philemon', 'Phlm', 'Phm', 'Pm', 'Filemón', 'Filemon', 'Philémon'],
    'heb': ['Hebrews', 'Heb', 'He', 'Hebreos', 'Hebräer', 'Hebraeer', 'Hebr', 'Hébreux', 'Hebreux'],
    'jas': ['James', 'Jas', 'Jm', 'Jam', 'Santiago', 'Stg', 'Jakobus', 'Jak', 'Jacques', 'Jacobi'],
    '1pe': ['1 Peter', '1Peter', '1 Pet', '1Pet', '1 Pe', '1Pe', '1 Pt', 'I Peter', 'First Peter', '1 Pedro', '1Pedro', '1 Petrus', '1. Petrus', '1Petr', '1 Pierre', '1Pierre'],
    '2pe': ['2 Peter', '2Peter', '2 Pet', '2Pet', '2 Pe', '2Pe', '2 Pt', 'II Peter', 'Second Peter', '2 Pedro', '2Pedro', '2 Petrus', '2. Petrus', '2Petr', '2 Pierre', '2Pierre'],
    '1jn': ['1 John', '1John', '1 Jn', '1Jn', '1 Jo', '1 Joh', '1Joh', 'I John', 'First John', '1 Juan', '1Juan', '1 Johannes', '1. Johannes', '1 Jean', '1Jean'],
    '2jn': ['2 John', '2John', '2 Jn', '2Jn', '2 Jo', '2 Joh', '2Joh', 'II John', 'Second John', '2 Juan', '2Juan', '2 Johannes', '2. Johannes', '2 Jean', '2Jean'],
    '3jn': ['3 John', '3John', '3 Jn', '3Jn', '3 Jo', '3 Joh', '3Joh', 'III John', 'Third John', '3 Juan', '3Juan', '3 Johannes', '3. Johannes', '3 Jean', '3Jean'],
    'jud': ['Jude', 'Jud', 'Jd', 'Judas', 'Judae'],
    'rev': ['Revelation', 'Rev', 'Re', 'Rv', 'Revelations', 'Apocalypse', 'Apoc', 'Ap', 'Apocalipsis', 'Offenbarung', 'Offb', 'Apocalypsis'],
    '1es': ['1 Esdras', '1Esdras', '1 Esd', '1Esd', 'I Esdras', '3 Esdras', 'III Esdras'],
    '2es': ['2 Esdras', '2Esdras', '2 Esd', '2Esd', 'II Esdras', '4 Esdras', 'IV Esdras', '4 Ezra'],
    'esg': ['Esther (Greek)', 'Greek Esther', 'Esther Greek', 'Additions to Esther', 'Rest of Esther', 'Add Esth', 'AddEsth', 'EsG', 'Esg'],
    'pra': ['Prayer of Azariah', 'Azariah', 'PrAzar', 'Pr Azar', 'Song of the Three', 'Song of the Three Young Men', 'Song of the Three Children', 'Song of Three', 'S3Y', 'Three Youths'],
    'sus': ['Susanna', 'Sus'],
    'bel': ['Bel and the Dragon', 'Bel', 'Bel and Dragon'],
    'man': ['Prayer of Manasseh', 'Prayer of Manasses', 'Manasseh', 'Manasses', 'PrMan', 'Pr Man', 'Man'],
    'lje': ['Letter of Jeremiah', 'Epistle of Jeremiah', 'Epistle of Jeremy', 'Ep Jer', 'EpJer', 'LJe', 'Let Jer'],
    'ps151': ['Psalm 151', 'Ps 151', 'Ps151', 'Psalms 151'],
}

# ---------------------------------------------------------------- Vulgate psalm numbering
# Editions numbered after the Septuagint/Vulgate (Douay-Rheims, Clementine Vulgate) are remapped to the
# Hebrew (KJV) psalm numbers used as the work's canonical IDs. Verse numbers inside each psalm are kept as
# the edition has them (the Vulgate counts the title as verse 1).

def vulgate_psalm_to_hebrew(ch, verse):
    """Return (hebrew_psalm, verse) for a Vulgate (psalm, verse) pair."""
    if ch <= 8:
        return ch, verse
    if ch == 9:
        return (9, verse) if verse <= 21 else (10, verse - 21)
    if 10 <= ch <= 112:
        return ch + 1, verse
    if ch == 113:
        return (114, verse) if verse <= 8 else (115, verse - 8)
    if ch == 114:
        return 116, verse
    if ch == 115:
        return 116, verse + 9
    if 116 <= ch <= 145:
        return ch + 1, verse
    if ch == 146:
        return 147, verse
    if ch == 147:
        return 147, verse + 11
    return ch, verse

# ---------------------------------------------------------------- text helpers

_WS = re.compile(r'[ \t\r\f\v  -   　]+')

def clean_text(s):
    """NFC, single spaces, trimmed; keeps '\n' line breaks (collapsing runs and trimming each line)."""
    s = unicodedata.normalize('NFC', s)
    s = s.replace('​', '').replace('﻿', '')
    lines = [_WS.sub(' ', ln).strip() for ln in s.split('\n')]
    out = []
    for ln in lines:
        if ln == '':
            continue
        out.append(ln)
    return '\n'.join(out)

HTML_RE = re.compile(r'</?[a-z][^>]*>', re.I)

def assert_clean(text, where):
    if HTML_RE.search(text):
        raise ValueError(f'HTML in {where}: {text[:120]!r}')
    if text != unicodedata.normalize('NFC', text):
        raise ValueError(f'non-NFC in {where}')

# ---------------------------------------------------------------- writers

class Writer:
    """Collects passages per unit and writes one JSON file per unit; tracks counts and bytes."""

    def __init__(self, work_id, edition_id):
        self.work_id, self.edition_id = work_id, edition_id
        self.dir = os.path.join(WORKS, work_id, edition_id)
        os.makedirs(self.dir, exist_ok=True)
        self.units = {}          # unit -> list of passages (ordered)
        self.order = []
        self.passages = 0
        self.bytes = 0

    def add(self, unit, ref, text, heading=None, notes=None):
        assert ref.startswith(unit + ':'), (unit, ref)
        text = clean_text(text)
        if not text:
            return False
        assert_clean(text, ref)
        p = {'ref': ref, 'text': text}
        if heading:
            heading = clean_text(heading)
            if heading:
                assert_clean(heading, ref + ' heading')
                p['heading'] = heading
        if notes:
            for n in notes:                      # offsets computed before final whitespace cleanup may overshoot
                n['at'] = max(0, min(int(n.get('at', 0)), len(text)))
            p['notes'] = notes
        if unit not in self.units:
            self.units[unit] = []
            self.order.append(unit)
        self.units[unit].append(p)
        self.passages += 1
        return True

    def flush(self):
        for unit in self.order:
            passages = self.units[unit]
            if not passages:
                continue
            lines = [json.dumps(p, ensure_ascii=False) for p in passages]
            body = ('{ "workId": %s, "editionId": %s, "unit": %s,\n  "passages": [\n    %s\n  ] }\n'
                    % (json.dumps(self.work_id), json.dumps(self.edition_id), json.dumps(unit), ',\n    '.join(lines)))
            fp = os.path.join(self.dir, unit.replace(':', '-') + '.json')
            data = body.encode('utf-8')
            with open(fp, 'wb') as f:
                f.write(data)
            self.bytes += len(data)
        return len(self.order), self.passages, self.bytes


def write_manifest(work_id, manifest):
    fp = os.path.join(WORKS, work_id, 'manifest.json')
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with open(fp, 'wb') as f:
        f.write(data)
    return len(data)


def build_aliases(codes):
    out = {}
    for code in codes:
        seen = []
        for a in ALIASES.get(code, []) + [BOOK_NAMES[code]]:
            a = unicodedata.normalize('NFC', a).lower().strip()
            if a and a != code and a not in seen:
                seen.append(a)
        out[code] = seen
    return out
