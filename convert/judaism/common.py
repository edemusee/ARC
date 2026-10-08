"""Shared helpers for the Jewish text converters (tradition `judaism`).

Run with `python3 -I` from outside the source clones. Sources are untrusted data: Sefaria JSON is only
ever parsed with json.loads, and files are pulled one at a time out of the Sefaria-Export-Archive git
clone with `git show <commit>:json/<path>` (the clone is `--filter=blob:none --sparse`, so single-file
reads are the cheap path; never walk large subtrees).

Sefaria JSON layout: `text` is a jagged array nested per `sectionNames` (chapter → verse …), or, for
complex works such as a siddur, a dict tree whose keys are the schema's node `enTitle`s. Only NAMED
versions (file named after versionTitle) are used; `merged.json` is never read.
"""
import html
import json
import os
import re
import shutil
import subprocess
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.abspath(os.path.join(HERE, '..', '..'))
WORKS = os.path.join(READER, 'works')
SOURCES = os.environ.get(
    'JUDAISM_SOURCES',
    '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/judaism')
SEFARIA_REPO = os.path.join(SOURCES, 'Sefaria-Export-Archive')
SEFARIA_COMMIT = os.environ.get('SEFARIA_COMMIT', '0494cd32f')
SEFARIA_URL = 'https://github.com/Sefaria/Sefaria-Export-Archive'
HEBCAL_LEYNING = os.path.join(SOURCES, 'hebcal-leyning')
CACHE = os.path.join(os.path.dirname(SOURCES.rstrip('/')), 'extracted', 'judaism')

TRAD = 'judaism'

HE_EDITION = {'lang': 'he', 'script': 'Hebr', 'direction': 'rtl', 'font': 'hebrew'}
EN_EDITION = {'lang': 'en', 'script': 'Latn', 'direction': 'ltr'}

HTML_TAG = re.compile(r'</?[a-zA-Z][^>]*>')


# ---------- source access ----------
def sefaria_path(path):
    """Fetch one file from the archive at SEFARIA_COMMIT (cached on disk) and return the parsed JSON.
    `path` is relative to the repository root, e.g. 'json/Tanakh/Torah/Genesis/Hebrew/Tanach with
    Nikkud.json' or 'schemas/Psalms.json'."""
    cached = os.path.join(CACHE, path)
    if not os.path.exists(cached):
        os.makedirs(os.path.dirname(cached), exist_ok=True)
        r = subprocess.run(['git', '-C', SEFARIA_REPO, 'show', f'{SEFARIA_COMMIT}:{path}'],
                           capture_output=True)
        if r.returncode != 0:
            raise FileNotFoundError(f'{path}: {r.stderr.decode("utf-8", "replace").strip()}')
        with open(cached, 'wb') as f:
            f.write(r.stdout)
    with open(cached, encoding='utf-8') as f:
        return json.load(f)


def sefaria_version(category_path, lang_dir, version_title):
    """Load `json/<category_path>/<lang_dir>/<version_title>.json`. Sefaria strips ':' from file names
    and the archive drops some punctuation, so a couple of spellings are tried."""
    stripped = re.sub(r'[:()]', '', version_title)
    candidates = [version_title, version_title.replace(':', ''), stripped, re.sub(r' {2,}', ' ', stripped)]
    last = None
    for c in candidates:
        try:
            return sefaria_path(f'json/{category_path}/{lang_dir}/{c}.json')
        except FileNotFoundError as e:
            last = e
    raise last


def source_url(category_path, lang_dir, version_title):
    return f'{SEFARIA_URL} (json/{category_path}/{lang_dir}/{version_title}.json @ {SEFARIA_COMMIT})'


# ---------- text cleaning ----------
def norm(text):
    """NFC, collapse whitespace runs to one space (line breaks kept), trim."""
    if text is None:
        return ''
    t = unicodedata.normalize('NFC', str(text))
    t = t.replace(' ', ' ').replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'[ \t​﻿]+', ' ', t)
    t = '\n'.join(line.strip() for line in t.split('\n'))
    t = re.sub(r'\n{2,}', '\n', t)
    t = re.sub(r' ([,.;:!?])', r'\1', t)
    t = re.sub(r'\( +', '(', t)
    t = re.sub(r' +\)', ')', t)
    return t.strip()


def _markup(t, tag, mark):
    """<tag>x</tag> → mark x mark, keeping the marks tight against the content and dropping empty pairs."""
    def rep(m):
        inner = m.group(1)
        lead = len(inner) - len(inner.lstrip())
        trail = len(inner) - len(inner.rstrip())
        core = inner.strip()
        if not core:
            return inner
        return inner[:lead] + mark + core + mark + inner[len(inner) - trail:] if trail else inner[:lead] + mark + core + mark
    return re.sub(rf'<{tag}(?:\s[^>]*)?>(.*?)</{tag}>', rep, t, flags=re.S | re.I)


def clean(text, bold=True, italic=True):
    """Sefaria HTML → reader plain text with the allowed inline markup.
    <b>/<strong> → **…**, <i>/<em> → *…*, <br> → newline, every other tag removed, entities unescaped.
    Footnote markers (<sup class="footnote-marker">) and inline footnotes (<i class="footnote">) are dropped."""
    t = str(text)
    t = re.sub(r'<sup[^>]*class="footnote-marker"[^>]*>.*?</sup>', '', t, flags=re.S | re.I)
    t = re.sub(r'<i[^>]*class="footnote"[^>]*>.*?</i>', '', t, flags=re.S | re.I)
    t = re.sub(r'<sup[^>]*>.*?</sup>', '', t, flags=re.S | re.I)
    t = re.sub(r'<br\s*/?>', '\n', t, flags=re.I)
    t = re.sub(r'</p>\s*<p[^>]*>', '\n', t, flags=re.I)
    for tag in ('b', 'strong'):
        t = _markup(t, tag, '**' if bold else '')
    for tag in ('i', 'em'):
        t = _markup(t, tag, '*' if italic else '')
    t = HTML_TAG.sub('', t)
    t = html.unescape(t)
    t = t.replace('****', '')
    return norm(t)


def strip_tags(text):
    return norm(html.unescape(HTML_TAG.sub('', re.sub(r'<br\s*/?>', '\n', str(text), flags=re.I))))


def slugify(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii').lower()
    s = re.sub(r"['’]", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def slug_ok(s):
    return re.fullmatch(r'[a-z0-9-]+', s) is not None


# ---------- output ----------
def reset_work(work_id):
    d = os.path.join(WORKS, work_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def write_manifest(work_id, manifest):
    with open(os.path.join(WORKS, work_id, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write('\n')


def write_unit(work_id, edition_id, unit, passages):
    """Write one unit file; returns the number of passages written (0 = nothing written)."""
    passages = [p for p in passages if p.get('text')]
    if not passages:
        return 0
    for p in passages:
        assert p['ref'] == unit or p['ref'].startswith(unit + ':'), (work_id, edition_id, unit, p['ref'])
    d = os.path.join(WORKS, work_id, edition_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, unit.replace(':', '-') + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'workId': work_id, 'editionId': edition_id, 'unit': unit, 'passages': passages},
                  f, ensure_ascii=False, separators=(',', ':'))
    return len(passages)


def passage(ref, text, heading=None):
    p = {'ref': ref, 'text': text}
    if heading:
        p['heading'] = heading
    return p


def edition(eid, base, label, role, license_, source, notes=None, **extra):
    e = {'id': eid, **base, 'label': {'en': label}, 'role': role, 'license': license_, 'source': source}
    if notes:
        e['notes'] = {'en': notes}
    e.update(extra)
    return e


def license_text(version_json, fallback='unknown'):
    """The license string the Sefaria version file states."""
    lic = version_json.get('license') or fallback
    return str(lic)


def report(work_id, counts):
    print(f'{work_id}: ' + ', '.join(f'{k}={v}' for k, v in counts.items()))
