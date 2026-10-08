"""Tanakh → works/tanakh (Bible-like manifest, 39 books in Tanakh order, Hebrew versification).

Editions: he-nikud (Tanach with Nikkud), he-taamim (Tanach with Ta'amei Hamikra), en-jps1917 (JPS 1917).
All three follow the Hebrew chapter/verse numbering (JPS 1917 counts psalm superscriptions as verses), so
no remapping is done.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, clean, edition, license_text, passage, report, reset_work,
                    sefaria_version, source_url, write_manifest, write_unit)

WORK = 'tanakh'

# (code, Sefaria folder, English name, Sefaria section) in Tanakh order
BOOKS = [
    ('gen', 'Genesis', 'Genesis', 'Torah'), ('exo', 'Exodus', 'Exodus', 'Torah'),
    ('lev', 'Leviticus', 'Leviticus', 'Torah'), ('num', 'Numbers', 'Numbers', 'Torah'),
    ('deu', 'Deuteronomy', 'Deuteronomy', 'Torah'),
    ('jos', 'Joshua', 'Joshua', 'Prophets'), ('jdg', 'Judges', 'Judges', 'Prophets'),
    ('1sa', 'I Samuel', '1 Samuel', 'Prophets'), ('2sa', 'II Samuel', '2 Samuel', 'Prophets'),
    ('1ki', 'I Kings', '1 Kings', 'Prophets'), ('2ki', 'II Kings', '2 Kings', 'Prophets'),
    ('isa', 'Isaiah', 'Isaiah', 'Prophets'), ('jer', 'Jeremiah', 'Jeremiah', 'Prophets'),
    ('ezk', 'Ezekiel', 'Ezekiel', 'Prophets'), ('hos', 'Hosea', 'Hosea', 'Prophets'),
    ('jol', 'Joel', 'Joel', 'Prophets'), ('amo', 'Amos', 'Amos', 'Prophets'),
    ('oba', 'Obadiah', 'Obadiah', 'Prophets'), ('jon', 'Jonah', 'Jonah', 'Prophets'),
    ('mic', 'Micah', 'Micah', 'Prophets'), ('nam', 'Nahum', 'Nahum', 'Prophets'),
    ('hab', 'Habakkuk', 'Habakkuk', 'Prophets'), ('zep', 'Zephaniah', 'Zephaniah', 'Prophets'),
    ('hag', 'Haggai', 'Haggai', 'Prophets'), ('zec', 'Zechariah', 'Zechariah', 'Prophets'),
    ('mal', 'Malachi', 'Malachi', 'Prophets'),
    ('psa', 'Psalms', 'Psalms', 'Writings'), ('pro', 'Proverbs', 'Proverbs', 'Writings'),
    ('job', 'Job', 'Job', 'Writings'), ('sng', 'Song of Songs', 'Song of Songs', 'Writings'),
    ('rut', 'Ruth', 'Ruth', 'Writings'), ('lam', 'Lamentations', 'Lamentations', 'Writings'),
    ('ecc', 'Ecclesiastes', 'Ecclesiastes', 'Writings'), ('est', 'Esther', 'Esther', 'Writings'),
    ('dan', 'Daniel', 'Daniel', 'Writings'), ('ezr', 'Ezra', 'Ezra', 'Writings'),
    ('neh', 'Nehemiah', 'Nehemiah', 'Writings'), ('1ch', 'I Chronicles', '1 Chronicles', 'Writings'),
    ('2ch', 'II Chronicles', '2 Chronicles', 'Writings'),
]

ALIASES = {
    'gen': ['genesis', 'gen', 'gn', 'ge', 'bereshit', 'bereishit', 'breishit', 'bereshis', 'beresheet'],
    'exo': ['exodus', 'exo', 'ex', 'shemot', 'shmot', 'shemos'],
    'lev': ['leviticus', 'lev', 'lv', 'vayikra', 'vayyikra', 'vayikro'],
    'num': ['numbers', 'num', 'nm', 'nu', 'bamidbar', 'bemidbar'],
    'deu': ['deuteronomy', 'deut', 'deu', 'dt', 'devarim', 'dvarim', 'devorim'],
    'jos': ['joshua', 'josh', 'jos', 'yehoshua', 'yehoshuah'],
    'jdg': ['judges', 'judg', 'jdg', 'shoftim', 'shofetim'],
    '1sa': ['1 samuel', '1samuel', '1 sam', '1sam', 'i samuel', 'shmuel 1', 'shmuel i', '1 shmuel', 'shmuel aleph', 'shemuel 1', '1 shemuel'],
    '2sa': ['2 samuel', '2samuel', '2 sam', '2sam', 'ii samuel', 'shmuel 2', 'shmuel ii', '2 shmuel', 'shmuel bet', 'shemuel 2', '2 shemuel'],
    '1ki': ['1 kings', '1kings', '1 kgs', '1kgs', 'i kings', 'melachim 1', 'melachim i', '1 melachim', 'melachim aleph', 'melakhim 1', '1 melakhim'],
    '2ki': ['2 kings', '2kings', '2 kgs', '2kgs', 'ii kings', 'melachim 2', 'melachim ii', '2 melachim', 'melachim bet', 'melakhim 2', '2 melakhim'],
    'isa': ['isaiah', 'isa', 'is', 'yeshayahu', 'yeshaya', 'yeshayah'],
    'jer': ['jeremiah', 'jer', 'yirmiyahu', 'yirmiyah', 'yirmeyahu'],
    'ezk': ['ezekiel', 'ezek', 'ezk', 'yechezkel', 'yehezkel'],
    'hos': ['hosea', 'hos', 'hoshea'],
    'jol': ['joel', 'jol', 'yoel'],
    'amo': ['amos', 'amo'],
    'oba': ['obadiah', 'obad', 'oba', 'ovadiah', 'ovadia', 'ovadyah'],
    'jon': ['jonah', 'jon', 'yonah', 'yona'],
    'mic': ['micah', 'mic', 'michah', 'mikhah'],
    'nam': ['nahum', 'nah', 'nam', 'nachum'],
    'hab': ['habakkuk', 'hab', 'chavakuk', 'havakuk', 'chabakuk'],
    'zep': ['zephaniah', 'zeph', 'zep', 'tzefaniah', 'tzefania', 'tzephaniah'],
    'hag': ['haggai', 'hag', 'chaggai', 'chagai'],
    'zec': ['zechariah', 'zech', 'zec', 'zechariyah', 'zekharia', 'zecharia'],
    'mal': ['malachi', 'mal', 'malakhi'],
    'psa': ['psalms', 'psalm', 'ps', 'pss', 'psa', 'tehillim', 'tehilim', 'tehillin'],
    'pro': ['proverbs', 'prov', 'pro', 'mishlei', 'mishle', 'mishley'],
    'job': ['job', 'iyov', 'iyyov', 'eyov'],
    'sng': ['song of songs', 'song of solomon', 'song', 'sng', 'canticles', 'shir hashirim', 'shir ha-shirim', 'shir hashirim'],
    'rut': ['ruth', 'rut', 'rus'],
    'lam': ['lamentations', 'lam', 'eicha', 'eichah', 'eikhah', 'ekhah'],
    'ecc': ['ecclesiastes', 'eccl', 'ecc', 'kohelet', 'koheleth', 'qohelet'],
    'est': ['esther', 'est', 'esth', 'ester', 'megillat esther'],
    'dan': ['daniel', 'dan', 'daniyel'],
    'ezr': ['ezra', 'ezr'],
    'neh': ['nehemiah', 'neh', 'nechemiah', 'nechemia', 'nehemya'],
    '1ch': ['1 chronicles', '1chronicles', '1 chr', '1chr', 'i chronicles', 'divrei hayamim 1', 'divrei hayamim i', '1 divrei hayamim', 'divrei hayamim aleph', 'divrei ha-yamim 1'],
    '2ch': ['2 chronicles', '2chronicles', '2 chr', '2chr', 'ii chronicles', 'divrei hayamim 2', 'divrei hayamim ii', '2 divrei hayamim', 'divrei hayamim bet', 'divrei ha-yamim 2'],
}

EDITIONS = [
    # id, lang dir, versionTitle, base, label, role
    ('he-nikud', 'Hebrew', 'Tanach with Nikkud', HE_EDITION, 'Hebrew — Tanach with Nikkud', 'original'),
    ('he-taamim', 'Hebrew', "Tanach with Ta'amei Hamikra", HE_EDITION, 'Hebrew — Tanach with Ta\'amei Hamikra (cantillation)', 'original'),
    ('en-jps1917', 'English', 'The Holy Scriptures: A New Translation (JPS 1917)', EN_EDITION, 'English — JPS 1917', 'translation'),
]


def load_book(code, folder, section, lang_dir, version_title):
    return sefaria_version(f'Tanakh/{section}/{folder}', lang_dir, version_title)


def main():
    reset_work(WORK)
    books, chapters, he_names = {}, {}, {}
    counts = {'units': 0, 'passages': 0}
    licenses = {}
    for eid, lang_dir, vt, base, label, role in EDITIONS:
        for code, folder, en_name, section in BOOKS:
            d = load_book(code, folder, section, lang_dir, vt)
            licenses.setdefault(eid, license_text(d))
            text = d['text']
            if d.get('heTitle'):
                he_names.setdefault(code, d['heTitle'])
            books.setdefault(code, {'en': en_name})
            n_ch = len(text)
            chapters[code] = max(chapters.get(code, 0), n_ch)
            for ci, verses in enumerate(text, 1):
                ps = []
                for vi, v in enumerate(verses or [], 1):
                    t = clean(v)
                    if t:
                        ps.append(passage(f'{code}:{ci}:{vi}', t))
                n = write_unit(WORK, eid, f'{code}:{ci}', ps)
                if n:
                    counts['units'] += 1
                    counts['passages'] += n
    for code in books:
        if code in he_names:
            books[code]['he'] = he_names[code]
    order = [b[0] for b in BOOKS]
    manifest = {
        'schemaVersion': 1,
        'workId': WORK, 'tradition': 'judaism', 'shelf': 'scripture', 'families': [],
        'title': {'en': 'Tanakh', 'he': 'תנ״ך'},
        'subtitle': {'en': 'Torah, Nevi\'im and Ketuvim — the Hebrew Bible in the traditional Jewish order'},
        'levels': [
            {'id': 'book', 'label': {'en': 'Book'}},
            {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
            {'id': 'verse', 'label': {'en': 'Verse'}},
        ],
        'citation': {'format': '{book} {chapter}:{verse}', 'rangeFormat': '{book} {chapter}:{verse}–{verse2}',
                     'workAbbrev': {'en': ''}},
        'canons': {'tanakh-24': order},
        'books': {c: books[c] for c in order},
        'chapters': {c: chapters[c] for c in order},
        'editions': [
            edition(eid, base, label, role, licenses[eid],
                    source_url('Tanakh/<section>/<book>', lang_dir, vt),
                    notes=notes, canon='tanakh-24')
            for (eid, lang_dir, vt, base, label, role), notes in zip(EDITIONS, [
                'Vocalized Hebrew text (tanach.us Westminster Leningrad Codex transcription via Sefaria). Hebrew chapter and verse numbering throughout.',
                'Hebrew text with vowel points and cantillation marks (te\'amim); otherwise identical to the Nikkud edition.',
                'The Jewish Publication Society 1917 translation, digitised by the Open Siddur Project. Follows the Hebrew verse numbering, so psalm superscriptions are verse 1.',
            ])
        ],
        'defaultEditions': ['he-nikud', 'en-jps1917'],
        'aliases': ALIASES,
        'notes': {'en': 'The 24 books of the Hebrew canon, with Samuel, Kings, Chronicles and Ezra–Nehemiah split as in printed editions (39 entries).'},
    }
    write_manifest(WORK, manifest)
    report(WORK, counts)


if __name__ == '__main__':
    main()
