#!/usr/bin/env python3
"""Convert Christian creeds, confessions and catechisms into works/<workId>/ (shelf `documents`).

Sources (untrusted data, parsed only):
  Creeds.json            <SOURCES>/Creeds.json/creeds/*.json           (public-domain items only)
  open-christian-data    <SOURCES>/open-christian-data/data/{catechisms,doctrinal-documents}/
  open-prayer-book       <SOURCES>/open-prayer-book/md/bcp1662.md      (Articles of Religion)

Usage: python3 -I convert_documents.py [workId ...]
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CREEDS_JSON, CREEDS_JSON_LICENSE, CREEDS_JSON_URL, OCD, OCD_LICENSE, OCD_URL, OPB,
                    OPB_LICENSE, OPB_URL, edition, load_json, norm, osis_to_text, paragraphs, proof_notes,
                    reset_work, roman_to_int, split_sentences, write_manifest, write_unit)

TRAD = 'christianity'
DONE = []


def base_manifest(work_id, title, subtitle, families, levels, citation, toc, editions, notes=None, aliases=None):
    m = {'schemaVersion': 1, 'workId': work_id, 'tradition': TRAD, 'shelf': 'documents', 'families': families,
         'title': {'en': title}}
    if subtitle:
        m['subtitle'] = {'en': subtitle}
    m['levels'] = levels
    m['citation'] = citation
    m['toc'] = toc
    m['editions'] = editions
    m['defaultEditions'] = [editions[0]['id']]
    if aliases:
        m['aliases'] = aliases
    if notes:
        m['notes'] = {'en': notes}
    return m


def creeds_edition(meta, ed_id='en', label='English'):
    src = CREEDS_JSON_URL + '/blob/master/creeds/' + meta['_file']
    lic = CREEDS_JSON_LICENSE
    attr = meta.get('SourceAttribution') or ''
    if attr.startswith('Public Domain - '):
        lic = 'Public domain; ' + attr[len('Public Domain - '):]
    return edition(ed_id, label, 'original' if meta.get('OriginalLanguage') == 'English' else 'translation', lic, src)


def load_creed(fname):
    d = load_json(os.path.join(CREEDS_JSON, fname))
    meta = d['Metadata']
    assert (meta.get('SourceAttribution') or '').startswith('Public Domain'), (fname, meta.get('SourceAttribution'))
    meta['_file'] = fname
    return meta, d['Data']


def subtitle_of(meta, extra=None):
    bits = []
    if extra:
        bits.append(extra)
    elif meta.get('Authors'):
        bits.append(', '.join(meta['Authors'][:2]))
    if meta.get('Year'):
        bits.append(str(meta['Year']))
    return ', '.join(bits)


# =====================================================================================
# Creeds: levels [section (isUnit), line]
# =====================================================================================
CREED_LEVELS = [{'id': 'section', 'label': {'en': 'Article'}, 'isUnit': True},
                {'id': 'line', 'label': {'en': 'Line'}}]


def creed_citation(abbrev):
    return {'format': '{work} {section}.{line}', 'rangeFormat': '{work} {section}.{line}–{line2}',
            'workAbbrev': {'en': abbrev}}


def convert_simple_creed(work_id, fname, title, subtitle, abbrev, sections=None, families=(), notes=None):
    """sections: list of (label, [lines]) — if None, one section per source paragraph, lines by sentence."""
    meta, data = load_creed(fname)
    reset_work(work_id)
    if sections is None:
        paras = paragraphs(data['Content'])
        if len(paras) == 1:
            sections = [('Text', split_sentences(paras[0]))]
        else:
            sections = [(f'Part {i + 1}', split_sentences(p)) for i, p in enumerate(paras)]
    toc = []
    for i, (label, lines) in enumerate(sections, 1):
        passages = [{'ref': f'{i}:{j}', 'text': norm(line)} for j, line in enumerate(lines, 1)]
        write_unit(work_id, 'en', str(i), passages)
        toc.append({'ref': str(i), 'label': {'en': label}, 'count': len(passages)})
    ed = creeds_edition(meta)
    ed['available'] = [t['ref'] for t in toc]
    write_manifest(work_id, base_manifest(work_id, title, subtitle or subtitle_of(meta), list(families), CREED_LEVELS,
                                          creed_citation(abbrev), toc, [ed], notes=notes))
    DONE.append((work_id, 'documents', list(families)))


def convert_apostles_creed():
    work_id = 'apostles-creed'
    meta, data = load_creed('apostles_creed.json')
    reset_work(work_id)
    # Traditional (BCP 1662, Morning Prayer) text, lined as in the original sample.
    traditional = [
        "I believe in God, the Father Almighty, Maker of heaven and earth:",
        "And in Jesus Christ his only Son our Lord;",
        "who was conceived by the Holy Ghost, born of the Virgin Mary,",
        "suffered under Pontius Pilate, was crucified, dead, and buried;",
        "he descended into hell;",
        "the third day he rose again from the dead;",
        "he ascended into heaven, and sitteth on the right hand of God the Father Almighty;",
        "from thence he shall come to judge the quick and the dead.",
        "I believe in the Holy Ghost;",
        "the holy catholic Church; the communion of saints;",
        "the forgiveness of sins;",
        "the resurrection of the body, and the life everlasting. Amen.",
    ]
    # Modern ecumenical text from Creeds.json, lined to match the traditional text.
    modern = [
        "I believe in God, the Father almighty, creator of heaven and earth.",
        "I believe in Jesus Christ, God's only Son, our Lord,",
        "who was conceived by the Holy Spirit, born of the Virgin Mary,",
        "suffered under Pontius Pilate, was crucified, died, and was buried;",
        "he descended to the dead.",
        "On the third day he rose again;",
        "he ascended into heaven, he is seated at the right hand of the Father,",
        "and he will come to judge the living and the dead.",
        "I believe in the Holy Spirit,",
        "the holy catholic Church, the communion of saints,",
        "the forgiveness of sins,",
        "the resurrection of the body, and the life everlasting. Amen.",
    ]
    src_text = re.sub(r'\s+', ' ', norm(data['Content']))
    assert ' '.join(modern) == src_text, 'Creeds.json Apostles\' Creed text changed; re-line it'
    write_unit(work_id, 'traditional', '1', [{'ref': f'1:{i}', 'text': t} for i, t in enumerate(traditional, 1)])
    write_unit(work_id, 'ecumenical', '1', [{'ref': f'1:{i}', 'text': t} for i, t in enumerate(modern, 1)])
    eds = [
        edition('traditional', 'Traditional English (Book of Common Prayer, 1662)', 'translation', OPB_LICENSE,
                OPB_URL + '/blob/master/md/bcp1662.md', available=['1']),
        edition('ecumenical', 'Modern English (ecumenical text)', 'translation', CREEDS_JSON_LICENSE,
                CREEDS_JSON_URL + '/blob/master/creeds/apostles_creed.json', available=['1']),
    ]
    m = base_manifest(work_id, "The Apostles' Creed", 'Old Roman Symbol, received form c. 710', [], CREED_LEVELS,
                      creed_citation("Apostles'"), [{'ref': '1', 'label': {'en': 'Text'}, 'count': 12}], eds,
                      notes='The two editions are lined alike so that they can be read side by side.')
    m['defaultEditions'] = ['traditional']
    write_manifest(work_id, m)
    DONE.append((work_id, 'documents', []))


def convert_nicene_creed():
    """Keeps the structure and text of the original sample (4 articles; Eastern text omits the filioque)."""
    work_id = 'nicene-creed'
    reset_work(work_id)
    sections = {
        '1': ['I believe in one God, the Father Almighty, Maker of heaven and earth, and of all things visible and invisible.'],
        '2': ['And in one Lord Jesus Christ, the only-begotten Son of God,',
              'begotten of the Father before all worlds;',
              'God of God, Light of Light, very God of very God;',
              'begotten, not made, being of one substance with the Father, by whom all things were made;',
              'who, for us men and for our salvation, came down from heaven,',
              'and was incarnate by the Holy Ghost of the Virgin Mary, and was made man;',
              'and was crucified also for us under Pontius Pilate; he suffered and was buried;',
              'and the third day he rose again, according to the Scriptures; and ascended into heaven, and sitteth on the right hand of the Father;',
              'and he shall come again, with glory, to judge both the quick and the dead; whose kingdom shall have no end.'],
        '3': ['And I believe in the Holy Ghost, the Lord and Giver of Life;',
              'who proceedeth from the Father and the Son;',
              'who with the Father and the Son together is worshipped and glorified;',
              'who spake by the prophets.'],
        '4': ['And I believe in one holy catholic and apostolic Church.',
              'I acknowledge one baptism for the remission of sins;',
              'and I look for the resurrection of the dead,',
              'and the life of the world to come. Amen.'],
    }
    labels = {'1': 'The Father', '2': 'The Son', '3': 'The Holy Spirit', '4': 'The Church'}
    for ed_id in ('with-filioque', 'without-filioque'):
        for sec, lines in sections.items():
            ps = []
            for j, line in enumerate(lines, 1):
                if ed_id == 'without-filioque' and sec == '3' and j == 2:
                    line = 'who proceedeth from the Father;'
                ps.append({'ref': f'{sec}:{j}', 'text': line})
            write_unit(work_id, ed_id, sec, ps)
    toc = [{'ref': s, 'label': {'en': labels[s]}, 'count': len(sections[s])} for s in sections]
    western = ['catholic', 'anglican', 'lutheran', 'reformed', 'baptist', 'methodist', 'pentecostal', 'anabaptist',
               'adventist', 'restoration', 'nondenominational']
    src = 'Schaff, Creeds of Christendom (via ' + CREEDS_JSON_URL + '/blob/master/creeds/nicene_creed.json)'
    eds = [
        edition('with-filioque', 'Western text (with filioque)', 'translation', CREEDS_JSON_LICENSE, src,
                families=western, available=list(sections)),
        edition('without-filioque', 'Eastern text (without filioque)', 'translation', CREEDS_JSON_LICENSE, src,
                families=['eastern-orthodox', 'oriental-orthodox'], available=list(sections)),
    ]
    m = base_manifest(work_id, 'The Nicene Creed', 'Niceno-Constantinopolitan Creed, 381', [], CREED_LEVELS,
                      creed_citation('Nicene'), toc, eds,
                      notes='The two texts differ in article 3, line 2. Both are shown side by side by default.')
    m['defaultEditions'] = ['with-filioque', 'without-filioque']
    write_manifest(work_id, m)
    DONE.append((work_id, 'documents', []))


def convert_nicene_325():
    work_id = 'nicene-creed-325'
    d = load_json(os.path.join(OCD, 'doctrinal-documents', 'nicene-creed-325.json'))
    text = norm(d['data']['units'][0]['content'])
    # The concluding anathemas are in Schaff's square brackets; keep them as a second article.
    m = re.search(r'\s*\[But those who say.*\]\s*$', text, re.S)
    creed, anath = (text[:m.start()].strip(), m.group(0).strip()) if m else (text, None)
    reset_work(work_id)
    lines = split_sentences(creed)
    write_unit(work_id, 'en', '1', [{'ref': f'1:{i}', 'text': l} for i, l in enumerate(lines, 1)])
    toc = [{'ref': '1', 'label': {'en': 'The Creed'}, 'count': len(lines)}]
    if anath:
        write_unit(work_id, 'en', '2', [{'ref': '2:1', 'text': anath.strip('[]').strip()}])
        toc.append({'ref': '2', 'label': {'en': 'The Anathemas'}, 'count': 1})
    ed = edition('en', 'English (Schaff, Creeds of Christendom)', 'translation', OCD_LICENSE,
                 OCD_URL + '/blob/main/data/doctrinal-documents/nicene-creed-325.json', available=[t['ref'] for t in toc])
    write_manifest(work_id, base_manifest(work_id, 'The Creed of Nicaea (325)', 'First Council of Nicaea, 325', [],
                                          CREED_LEVELS, creed_citation('Nicaea 325'), toc, [ed],
                                          notes='The original creed of 325 with its concluding anathemas; square brackets are Schaff\'s.'))
    DONE.append((work_id, 'documents', []))


# =====================================================================================
# Confessions with chapters and numbered sections: levels [chapter (isUnit), section]
# =====================================================================================
def chapter_id(s):
    s = str(s).strip().lower().replace('&', '-').replace(' ', '')
    return re.sub(r'[^a-z0-9-]', '', s)


def section_subheading(content):
    """Second Helvetic style: an upper-case first paragraph is a sub-heading."""
    paras = paragraphs(content)
    if len(paras) > 1 and len(paras[0]) < 120:
        letters = [c for c in paras[0] if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) / len(letters) >= 0.6:
            return title_case(paras[0]), '\n\n'.join(paras[1:])
    return None, '\n\n'.join(paras)


def convert_confession(work_id, fname, title, subtitle, abbrev, families, chapter_label='Chapter', notes=None,
                       dort=False):
    meta, data = load_creed(fname)
    reset_work(work_id)
    toc = []
    for ch in data:
        cid = chapter_id(ch['Chapter'])
        ctitle = norm(ch['Title'])
        passages = []
        seen_r = False
        for i, s in enumerate(ch['Sections']):
            sid = chapter_id(s['Section'])
            content = re.sub(r'^\s*\d+\.\*\*\s*', '', s['Content'])  # stray markdown in Second Helvetic 9.1, 14.1
            sub, body = section_subheading(content)
            text, notes_ = (None, None)
            if s.get('ContentWithProofs') and s.get('Proofs'):
                text, notes_ = proof_notes(s['ContentWithProofs'], s['Proofs'])
                if text and re.sub(r'\s+', ' ', text) != re.sub(r'\s+', ' ', norm(body)):
                    text, notes_ = None, None   # marked text diverged from plain text; keep plain
            p = {'ref': f'{cid}:{sid}', 'text': text or norm(body)}
            heading = None
            if i == 0:
                heading = ctitle
            if dort and sid.startswith('r') and not seen_r:
                heading = 'Rejection of Errors'
                seen_r = True
            if sub:
                heading = f'{heading} — {sub}' if heading else sub
            if heading:
                p['heading'] = heading
            if notes_:
                p['notes'] = notes_
            passages.append(p)
        write_unit(work_id, 'en', cid, passages)
        label = ch['Chapter'].replace('&', ' & ') if dort else ch['Chapter']
        toc.append({'ref': cid, 'label': {'en': f'{label}. {ctitle}'}, 'count': len(passages)})
    ed = creeds_edition(meta)
    ed['available'] = [t['ref'] for t in toc]
    levels = [{'id': 'chapter', 'label': {'en': chapter_label}, 'isUnit': True},
              {'id': 'section', 'label': {'en': 'Section'}}]
    cit = {'format': '{work} {chapter}.{section}', 'rangeFormat': '{work} {chapter}.{section}–{section2}',
           'workAbbrev': {'en': abbrev}}
    write_manifest(work_id, base_manifest(work_id, title, subtitle or subtitle_of(meta), families, levels, cit, toc,
                                          [ed], notes=notes))
    DONE.append((work_id, 'documents', families))


# =====================================================================================
# Article-based documents ("Canon" format): either [article (isUnit), paragraph] or, for short
# documents, a single unit [part (isUnit), article].
# =====================================================================================
SPECIAL_ARTICLE = {'p': ('preface', 'Preface'), 'i': ('intro', 'Introduction'), 'c': ('conclusion', 'Conclusion')}


def article_ids(data):
    """Map the source Article ids ('1', 'IV', 'P', 'I', 'C') to ASCII ids and default labels."""
    raw = [str(a['Article']).strip() for a in data]
    uses_roman = (not any(r.isdigit() for r in raw)
                  and sum(1 for r in raw if r.lower() not in ('p', 'i', 'c') and roman_to_int(r)) >= 2)
    ids = []
    for r, a in zip(raw, data):
        key = r.lower()
        title = norm(a.get('Title') or '').lower()
        if key.isdigit():
            ids.append((key, f'Article {r}'))
        elif key in SPECIAL_ARTICLE and (not uses_roman or key != 'i' or title in ('introduction', 'exordium')):
            ids.append(SPECIAL_ARTICLE[key])
        elif roman_to_int(r):
            ids.append((str(roman_to_int(r)), f'Article {roman_to_int(r)}'))
        else:
            ids.append((re.sub(r'[^a-z0-9-]', '', key) or f'x{len(ids)}', f'Article {r}'))
    assert len({i for i, _ in ids}) == len(ids), ('duplicate article ids', ids)
    return ids


def article_label(a, default):
    t = norm(a.get('Title') or '')
    if not t:
        return default
    if re.fullmatch(r'(Article|Canon|Thesis|Art\.?)\s+[IVXLC0-9]+\.?', t, re.I) or re.fullmatch(r'[IVXLC]+\.?', t):
        return t if t.lower().startswith(('canon', 'thesis')) else default
    if t == t.upper() and any(c.isalpha() for c in t):
        t = title_case(t)
    return t


def convert_articles(work_id, fname, title, subtitle, abbrev, families, single_unit=None, notes=None,
                     article_label_name='Article'):
    meta, data = load_creed(fname)
    reset_work(work_id)
    total = sum(len(a['Content']) for a in data)
    if single_unit is None:
        single_unit = total < 15000
    ids = article_ids(data)
    toc = []
    ed = creeds_edition(meta)
    if single_unit:
        passages = []
        for (aid, default_label), a in zip(ids, data):
            text, notes_ = None, None
            if a.get('ContentWithProofs') and a.get('Proofs'):
                text, notes_ = proof_notes(a['ContentWithProofs'], a['Proofs'])
                if text and re.sub(r'\s+', ' ', text) != re.sub(r'\s+', ' ', norm(a['Content'])):
                    text, notes_ = None, None
            p = {'ref': f'1:{aid}', 'text': text or norm(a['Content']), 'heading': article_label(a, default_label)}
            if notes_:
                p['notes'] = notes_
            passages.append(p)
        write_unit(work_id, 'en', '1', passages)
        toc = [{'ref': '1', 'label': {'en': 'Text'}, 'count': len(passages)}]
        levels = [{'id': 'part', 'label': {'en': 'Part'}, 'isUnit': True},
                  {'id': 'article', 'label': {'en': article_label_name}}]
        ab = {'Article': 'art.', 'Thesis': 'thesis', 'Canon': 'canon'}.get(article_label_name, article_label_name.lower())
        cit = {'format': '{work} ' + ab + ' {article}', 'rangeFormat': '{work} ' + ab + ' {article}–{article2}',
               'workAbbrev': {'en': abbrev}}
    else:
        for (aid, default_label), a in zip(ids, data):
            paras = paragraphs(a['Content'])
            label = article_label(a, default_label)
            passages = []
            for j, para in enumerate(paras, 1):
                p = {'ref': f'{aid}:{j}', 'text': para}
                if j == 1:
                    p['heading'] = label
                passages.append(p)
            write_unit(work_id, 'en', aid, passages)
            tlabel = label if label == default_label or not aid.isdigit() else f'{aid}. {label}'
            toc.append({'ref': aid, 'label': {'en': tlabel}, 'count': len(passages)})
        levels = [{'id': 'article', 'label': {'en': article_label_name}, 'isUnit': True},
                  {'id': 'paragraph', 'label': {'en': 'Paragraph'}}]
        cit = {'format': '{work} {article}.{paragraph}', 'rangeFormat': '{work} {article}.{paragraph}–{paragraph2}',
               'workAbbrev': {'en': abbrev}}
    ed['available'] = [t['ref'] for t in toc]
    write_manifest(work_id, base_manifest(work_id, title, subtitle or subtitle_of(meta), families, levels, cit, toc,
                                          [ed], notes=notes))
    DONE.append((work_id, 'documents', families))


# =====================================================================================
# Catechisms: levels [part (isUnit), question]; part = block of 20 questions (or Lord's Days)
# =====================================================================================
HEIDELBERG_LORDS_DAYS = [(1, 2), (3, 5), (6, 8), (9, 11), (12, 15), (16, 19), (20, 23), (24, 25), (26, 26), (27, 28),
                         (29, 30), (31, 32), (33, 34), (35, 36), (37, 39), (40, 44), (45, 45), (46, 49), (50, 52),
                         (53, 53), (54, 56), (57, 58), (59, 61), (62, 64), (65, 68), (69, 71), (72, 74), (75, 77),
                         (78, 79), (80, 82), (83, 85), (86, 87), (88, 91), (92, 95), (96, 98), (99, 100), (101, 102),
                         (103, 103), (104, 104), (105, 107), (108, 109), (110, 111), (112, 112), (113, 115),
                         (116, 119), (120, 121), (122, 122), (123, 123), (124, 124), (125, 125), (126, 126),
                         (127, 129)]


def qa_passage(ref, number, question, answer, awp=None, proofs=None, heading_prefix='Q.'):
    text, notes_ = None, None
    if awp and proofs:
        text, notes_ = proof_notes(awp, proofs)
        if text and norm(answer) and re.sub(r'\s+', ' ', text) != re.sub(r'\s+', ' ', norm(answer)):
            text, notes_ = None, None
    elif awp and not norm(answer):           # a few source rows have the answer only in AnswerWithProofs
        text = norm(re.sub(r'\[\d+\]', '', awp))
    p = {'ref': ref, 'heading': f'{heading_prefix} {number}. {norm(question)}' if number is not None else norm(question),
         'text': text or norm(answer)}
    if notes_:
        p['notes'] = notes_
    return p


def convert_catechism(work_id, fname, title, subtitle, abbrev, families, lords_days=False, notes=None):
    meta, data = load_creed(fname)
    reset_work(work_id)
    qs = [(int(q['Number']), q) for q in data]
    assert [n for n, _ in qs] == list(range(1, len(qs) + 1)), (work_id, 'non-sequential numbering')
    if lords_days:
        groups = [(str(i), f'Lord\'s Day {i} (Q. {a}–{b})' if a != b else f'Lord\'s Day {i} (Q. {a})', a, b)
                  for i, (a, b) in enumerate(HEIDELBERG_LORDS_DAYS, 1)]
        assert groups[-1][3] == len(qs)
        level = {'id': 'lordsday', 'label': {'en': "Lord's Day"}, 'isUnit': True}
    else:
        n_parts = math.ceil(len(qs) / 20)
        groups = [(str(i), f'Questions {(i - 1) * 20 + 1}–{min(i * 20, len(qs))}', (i - 1) * 20 + 1, min(i * 20, len(qs)))
                  for i in range(1, n_parts + 1)]
        level = {'id': 'part', 'label': {'en': 'Part'}, 'isUnit': True}
    toc = []
    for gid, label, a, b in groups:
        passages = [qa_passage(f'{gid}:{n}', n, q['Question'], q['Answer'], q.get('AnswerWithProofs'), q.get('Proofs'))
                    for n, q in qs if a <= n <= b]
        write_unit(work_id, 'en', gid, passages)
        toc.append({'ref': gid, 'label': {'en': label}, 'count': len(passages)})
    ed = creeds_edition(meta)
    ed['available'] = [t['ref'] for t in toc]
    levels = [level, {'id': 'question', 'label': {'en': 'Question'}}]
    cit = {'format': '{work} Q. {question}', 'rangeFormat': '{work} Q. {question}–{question2}', 'workAbbrev': {'en': abbrev}}
    write_manifest(work_id, base_manifest(work_id, title, subtitle or subtitle_of(meta), families, levels, cit, toc,
                                          [ed], notes=notes))
    DONE.append((work_id, 'documents', families))


def convert_expository_catechism(work_id, fname, title, subtitle, abbrev, families, notes=None):
    """'HenrysCatechism' format: each main question with its sub-questions → unit per main question."""
    meta, data = load_creed(fname)
    reset_work(work_id)
    toc, used = [], set()
    units = []        # [uid, question, passages, sub_used, section_letter]
    for q in data:
        num = str(q['Number']).strip()
        if num.isdigit():
            assert num not in used, (work_id, num)
            used.add(num)
            units.append([num, norm(q['Question']), [qa_passage(f'{num}:0', num, q['Question'], q['Answer'])], set(), ''])
        else:
            # Flavel: unnumbered continuation sections ('?') belong to the preceding question; their
            # sub-questions get a letter prefix (a1, a2, … b1, …) so refs stay unique within the unit.
            u = units[-1]
            u[4] = chr(ord(u[4]) + 1) if u[4] else 'a'
            if norm(q['Question']) not in ('', '?') and norm(q['Answer']) not in ('', '?'):
                u[2].append(qa_passage(f'{u[0]}:{u[4]}0', None, q['Question'], q['Answer'], heading_prefix=''))
        uid, _, passages, sub_used, letter = units[-1]
        for s in q.get('SubQuestions') or []:
            sid = letter + (re.sub(r'[^a-z0-9]', '', str(s['Number']).lower()) or 'x')
            base, k = sid, 1
            while sid in sub_used:
                k += 1
                sid = f'{base}-{k}'
            sub_used.add(sid)
            if not norm(s.get('Answer')):
                continue
            passages.append(qa_passage(f'{uid}:{sid}', None, s['Question'], s['Answer'], heading_prefix=''))
    for uid, question, passages, _, _ in units:
        write_unit(work_id, 'en', uid, passages)
        toc.append({'ref': uid, 'label': {'en': f'Q. {uid}. {question}'}, 'count': len(passages)})
    ed = creeds_edition(meta)
    ed['available'] = [t['ref'] for t in toc]
    levels = [{'id': 'question', 'label': {'en': 'Question'}, 'isUnit': True},
              {'id': 'item', 'label': {'en': 'Item'}}]
    cit = {'format': '{work} {question}.{item}', 'rangeFormat': '{work} {question}.{item}–{item2}',
           'workAbbrev': {'en': abbrev}}
    write_manifest(work_id, base_manifest(work_id, title, subtitle or subtitle_of(meta), families, levels, cit, toc,
                                          [ed], notes=notes))
    DONE.append((work_id, 'documents', families))


# =====================================================================================
# open-christian-data catechisms (Luther, Baltimore)
# =====================================================================================
def ocd_edition(path_rel, label='English', role='original', lic=OCD_LICENSE):
    return edition('en', label, role, lic, OCD_URL + '/blob/main/data/' + path_rel)


def clean_ocd_text(t):
    t = norm(t)
    t = re.sub(r'\[\[pg-note-anchor:\d+\]\]', '', t)
    t = re.sub(r'\s*--\s*', '—', t)
    return norm(t)


def convert_luther():
    work_id = 'luther-small-catechism'
    d = load_json(os.path.join(OCD, 'catechisms', 'luthers-small-catechism.json'))
    reset_work(work_id)
    parts, order = {}, []
    for q in d['data']:
        bits = [norm(b) for b in q['group'].split(' -- ')]
        m = re.match(r'([IVX]+)\.\s*(.*)', bits[0])
        pid, ptitle = str(roman_to_int(m.group(1))), m.group(2)
        sub = ' — '.join(bits[1:])
        if pid not in parts:
            parts[pid] = (ptitle, [])
            order.append(pid)
        n = str(q['item_id'])
        heading = f'{sub} — Q. {n}. {clean_ocd_text(q["question"])}' if sub else f'Q. {n}. {clean_ocd_text(q["question"])}'
        parts[pid][1].append({'ref': f'{pid}:{n}', 'heading': heading, 'text': clean_ocd_text(q['answer'])})
    toc = []
    for pid in order:
        ptitle, ps = parts[pid]
        write_unit(work_id, 'en', pid, ps)
        toc.append({'ref': pid, 'label': {'en': f'{pid}. {ptitle}'}, 'count': len(ps)})
    ed = ocd_edition('catechisms/luthers-small-catechism.json', 'English (Robert E. Smith, Project Wittenberg, 2004)',
                     'translation', 'Public domain (translation released to the public domain by the translator); ' +
                     'Open Christian Data compilation CC BY-NC 4.0')
    ed['available'] = [t['ref'] for t in toc]
    levels = [{'id': 'part', 'label': {'en': 'Part'}, 'isUnit': True}, {'id': 'question', 'label': {'en': 'Question'}}]
    cit = {'format': '{work} {part}.{question}', 'rangeFormat': '{work} {part}.{question}–{question2}',
           'workAbbrev': {'en': 'Small Cat.'}}
    write_manifest(work_id, base_manifest(work_id, "Luther's Small Catechism", 'Martin Luther, 1529', ['lutheran'],
                                          levels, cit, toc, [ed],
                                          notes='Question numbering follows the Project Gutenberg edition, not the Book of Concord.'))
    DONE.append((work_id, 'documents', ['lutheran']))


BALTIMORE_EXTRA_LESSONS = [  # the source parser merged lessons 30–37 into lesson 29; split by first question
    (30, 315, 'On the First Commandment'),
    (31, 331, 'On the Honor and Invocation of the Saints'),
    (32, 345, 'On the Second and Third Commandments'),
    (33, 361, 'On the Fourth, Fifth, and Sixth Commandments'),
    (34, 373, 'On the Seventh, Eighth, Ninth, and Tenth Commandments'),
    (35, 389, 'On the First and Second Commandments of the Church'),
    (36, 397, 'On the Third, Fourth, Fifth, and Sixth Commandments of the Church'),
    (37, 408, 'On the Last Judgment and the Resurrection, Hell, Purgatory, and Heaven'),
]
ORDINALS = ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH', 'SIXTH', 'SEVENTH', 'EIGHTH', 'NINTH', 'TENTH', 'ELEVENTH',
            'TWELFTH', 'THIRTEENTH', 'FOURTEENTH', 'FIFTEENTH', 'SIXTEENTH', 'SEVENTEENTH', 'EIGHTEENTH',
            'NINETEENTH', 'TWENTIETH', 'TWENTY-FIRST', 'TWENTY-SECOND', 'TWENTY-THIRD', 'TWENTY-FOURTH',
            'TWENTY-FIFTH', 'TWENTY-SIXTH', 'TWENTY-SEVENTH', 'TWENTY-EIGHTH', 'TWENTY-NINTH']


def title_case(s):
    small = {'of', 'the', 'and', 'on', 'in', 'to', 'for', 'a', 'an', 'or', 'by', 'with', 'upon', 'his', 'its'}
    words = s.lower().split()
    return ' '.join(w if (i and w in small) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def convert_baltimore():
    work_id = 'baltimore-catechism'
    d = load_json(os.path.join(OCD, 'catechisms', 'baltimore-catechism-no-2.json'))
    reset_work(work_id)
    lessons = {}
    order = []
    for q in d['data']:
        n = int(q['item_id'])
        m = re.match(r'LESSON ([A-Z-]+):\s*(.*)', q['group'])
        lid = ORDINALS.index(m.group(1)) + 1
        ltitle = title_case(m.group(2))
        for xl, start, xt in BALTIMORE_EXTRA_LESSONS:
            if n >= start:
                lid, ltitle = xl, xt
        lid = str(lid)
        if lid not in lessons:
            lessons[lid] = (ltitle, [])
            order.append(lid)
        question = clean_ocd_text(q['question'])
        answer = clean_ocd_text(q['answer'] or '')
        if not answer and '? ' in question:   # one source row has the answer glued to the question
            question, answer = question.split('? ', 1)
            question += '?'
        if not answer:
            continue
        lessons[lid][1].append({'ref': f'{lid}:{n}', 'heading': f'Q. {n}. {question}', 'text': answer})
    toc = []
    for lid in order:
        t, ps = lessons[lid]
        write_unit(work_id, 'en', lid, ps)
        toc.append({'ref': lid, 'label': {'en': f'Lesson {lid}: {t}'}, 'count': len(ps)})
    ed = ocd_edition('catechisms/baltimore-catechism-no-2.json', 'English (1885 edition)')
    ed['available'] = [t['ref'] for t in toc]
    levels = [{'id': 'lesson', 'label': {'en': 'Lesson'}, 'isUnit': True}, {'id': 'question', 'label': {'en': 'Question'}}]
    cit = {'format': '{work} Q. {question}', 'rangeFormat': '{work} Q. {question}–{question2}', 'workAbbrev': {'en': 'Baltimore'}}
    write_manifest(work_id, base_manifest(work_id, 'Baltimore Catechism No. 2', 'Third Plenary Council of Baltimore, 1885',
                                          ['catholic'], levels, cit, toc, [ed]))
    DONE.append((work_id, 'documents', ['catholic']))


def convert_schleitheim():
    work_id = 'schleitheim'
    d = load_json(os.path.join(OCD, 'doctrinal-documents', 'schleitheim-confession-1527.json'))
    reset_work(work_id)
    toc = []
    for u in d['data']['units']:
        aid = str(roman_to_int(u['number']))
        paras = paragraphs(u['content'])
        ps = [{'ref': f'{aid}:{j}', 'text': p} for j, p in enumerate(paras, 1)]
        ps[0]['heading'] = norm(u['title'])
        write_unit(work_id, 'en', aid, ps)
        toc.append({'ref': aid, 'label': {'en': f'{aid}. {norm(u["title"])}'}, 'count': len(ps)})
    ed = ocd_edition('doctrinal-documents/schleitheim-confession-1527.json', 'English', 'translation')
    ed['available'] = [t['ref'] for t in toc]
    levels = [{'id': 'article', 'label': {'en': 'Article'}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}]
    cit = {'format': '{work} {article}.{paragraph}', 'rangeFormat': '{work} {article}.{paragraph}–{paragraph2}',
           'workAbbrev': {'en': 'Schleitheim'}}
    write_manifest(work_id, base_manifest(work_id, 'The Schleitheim Confession', 'Swiss Brethren (Michael Sattler), 1527',
                                          ['anabaptist'], levels, cit, toc, [ed]))
    DONE.append((work_id, 'documents', ['anabaptist']))


# =====================================================================================
# Thirty-nine Articles from the BCP 1662 markdown
# =====================================================================================
def md_clean(line):
    t = line
    t = re.sub(r'&amp;#160;|&#160;|&nbsp;', ' ', t)
    t = t.replace('&amp;', '&')
    t = re.sub(r'\*\*([A-Z][A-Z]+)\*\*', lambda m: m.group(1).capitalize(), t)  # drop-cap words
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
    t = re.sub(r'\.\.(\s|$)', r'.\1', t)
    return norm(t)


def table_lines(html):
    items = [norm(re.sub(r'<[^>]+>', '', x)) for x in re.findall(r'<em>(.*?)</em>', html)]
    out = []
    for it in items:
        if out and not re.search(r'[.;:]$', out[-1]):
            out[-1] = out[-1] + ' ' + it
        else:
            out.append(it)
    return out


def convert_thirty_nine_articles():
    work_id = 'thirty-nine-articles'
    with open(os.path.join(OPB, 'bcp1662.md'), encoding='utf-8') as f:
        md = f.read()
    start = md.index('## Articles of Religion')
    end = md.index('## A Table of Kindred and Affinity')
    sec = md[start:end]
    lines = sec.split('\n')
    units, cur = [], None
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        hm = re.match(r'^(?:####\s*)?([IVXL]+)\.\s*\*(.+?)\*\.?\s*$', line)
        if hm:
            cur = {'id': str(roman_to_int(hm.group(1))), 'title': norm(hm.group(2)).rstrip('.'), 'paras': []}
            units.append(cur)
        elif line.startswith('### **His Majesty'):
            cur = {'id': 'declaration', 'title': "His Majesty's Declaration", 'paras': []}
            units.append(cur)
        elif line.strip() == 'The Ratification.':
            cur = {'id': 'ratification', 'title': 'The Ratification', 'paras': []}
            units.append(cur)
        elif line.startswith('### **Articles of Religion'):
            cur = None  # table of articles → skip
        elif line.startswith('<table>'):
            html = ''
            while i < len(lines) and '</table>' not in lines[i]:
                html += lines[i]
                i += 1
            html += lines[i] if i < len(lines) else ''
            if cur is not None:
                cur['paras'].append('\n'.join(table_lines(html)))
        elif cur is not None and line.strip() and not line.startswith('<a ') and not line.startswith('#'):
            cur['paras'].append(md_clean(line))
        i += 1
    reset_work(work_id)
    toc = []
    assert [u['id'] for u in units if u['id'].isdigit()] == [str(n) for n in range(1, 40)], [u['id'] for u in units]
    for u in units:
        ps = [{'ref': f'{u["id"]}:{j}', 'text': p} for j, p in enumerate(u['paras'], 1) if p]
        ps[0]['heading'] = u['title']
        write_unit(work_id, 'en', u['id'], ps)
        label = f'{u["id"]}. {u["title"]}' if u['id'].isdigit() else u['title']
        toc.append({'ref': u['id'], 'label': {'en': label}, 'count': len(ps)})
    ed = edition('en', 'English (Book of Common Prayer, 1662)', 'original', OPB_LICENSE, OPB_URL + '/blob/master/md/bcp1662.md',
                 available=[t['ref'] for t in toc])
    levels = [{'id': 'article', 'label': {'en': 'Article'}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}]
    cit = {'format': '{work} {article}.{paragraph}', 'rangeFormat': '{work} {article}.{paragraph}–{paragraph2}',
           'workAbbrev': {'en': '39 Art.'}}
    write_manifest(work_id, base_manifest(work_id, 'The Thirty-nine Articles of Religion', 'Church of England, 1571 (1662 printing)',
                                          ['anglican'], levels, cit, toc, [ed]))
    DONE.append((work_id, 'documents', ['anglican']))


# =====================================================================================
ATHANASIAN_SECTIONS = None   # computed from the two source paragraphs


def convert_athanasian():
    meta, data = load_creed('athanasian_creed.json')
    paras = paragraphs(data['Content'])
    assert len(paras) == 2
    sections = [('Of the Trinity', split_sentences(paras[0])), ('Of the Incarnation', split_sentences(paras[1]))]
    convert_simple_creed('athanasian-creed', 'athanasian_creed.json', 'The Athanasian Creed', 'Quicunque Vult, c. 500–800',
                         'Athanasian', sections=sections)


R = ['reformed']
B = ['baptist']

JOBS = {
    # --- ecumenical creeds ---
    'apostles-creed': convert_apostles_creed,
    'nicene-creed': convert_nicene_creed,
    'nicene-creed-325': convert_nicene_325,
    'athanasian-creed': convert_athanasian,
    'chalcedon': lambda: convert_simple_creed('chalcedon', 'chalcedonian_definition.json', 'The Chalcedonian Definition',
                                              'Council of Chalcedon, 451', 'Chalcedon'),
    'gregory-declaration': lambda: convert_simple_creed('gregory-declaration', 'gregorys_declaration_of_faith.json',
                                                        "Gregory Thaumaturgus' Declaration of Faith", 'Gregory Thaumaturgus, c. 265',
                                                        'Gregory'),
    'ignatius-creed': lambda: convert_simple_creed('ignatius-creed', 'ignatius_creed.json', "Ignatius' Creed",
                                                   'Ignatius of Antioch, c. 110', 'Ignatius'),
    'irenaeus-rule': lambda: convert_simple_creed('irenaeus-rule', 'irenaeus_rule_of_faith.json', "Irenaeus' Rule of Faith",
                                                  'Irenaeus of Lyons, c. 180', 'Irenaeus'),
    'tertullian-rule': lambda: convert_simple_creed('tertullian-rule', 'tertullians_rule_of_faith.json', "Tertullian's Rule of Faith",
                                                    'Tertullian, c. 200', 'Tertullian'),
    # --- confessions with chapters/sections ---
    'westminster-confession': lambda: convert_confession('westminster-confession', 'westminster_confession_of_faith.json',
                                                         'The Westminster Confession of Faith', 'Westminster Assembly, 1647', 'WCF', R),
    'london-1689': lambda: convert_confession('london-1689', 'london_baptist_1689.json', 'The 1689 London Baptist Confession',
                                              'Second London Baptist Confession, 1677/1689', '2LBC', B),
    'second-helvetic': lambda: convert_confession('second-helvetic', 'second_helvetic_confession.json', 'The Second Helvetic Confession',
                                                  'Heinrich Bullinger, 1562/1566', '2nd Helv.', R),
    'dort': lambda: convert_confession('dort', 'canons_of_dort.json', 'The Canons of Dort', 'Synod of Dort, 1618–1619', 'Dort', R,
                                       chapter_label='Head of Doctrine', dort=True,
                                       notes='Sections a1… are the articles, r1… the Rejection of Errors; Heads III and IV are combined as in the original.'),
    # --- article-based confessions ---
    'heidelberg': lambda: convert_catechism('heidelberg', 'heidelberg_catechism.json', 'The Heidelberg Catechism',
                                            'Zacharias Ursinus and Caspar Olevianus, 1563', 'HC', R, lords_days=True),
    'belgic': lambda: convert_articles('belgic', 'belgic_confession_of_faith.json', 'The Belgic Confession', 'Guido de Brès, 1561',
                                       'Belgic', R, single_unit=False),
    'scots-confession': lambda: convert_articles('scots-confession', 'scots_confession.json', 'The Scots Confession',
                                                 'John Knox and others, 1560', 'Scots', R, single_unit=False),
    'french-confession': lambda: convert_articles('french-confession', 'french_confession_of_faith.json', 'The French Confession of Faith',
                                                  'Gallican Confession, 1559', 'French', R, single_unit=False,
                                                  notes='Includes the prefatory letter to the King.'),
    'tetrapolitan': lambda: convert_articles('tetrapolitan', 'tetrapolitan_confession.json', 'The Tetrapolitan Confession',
                                             'Martin Bucer and Wolfgang Capito, 1530', 'Tetrapolitan', R, single_unit=False),
    'zwingli-fidei-ratio': lambda: convert_articles('zwingli-fidei-ratio', 'zwinglis_fidei_ratio.json', "Zwingli's Fidei Ratio",
                                                    'Ulrich Zwingli, 1530 (Thomas Cotsforde\'s 1555 English)', 'Fidei Ratio', R,
                                                    single_unit=False, notes='Early-modern English spelling of the 1555 translation is retained.'),
    'first-helvetic': lambda: convert_articles('first-helvetic', 'first_helvetic_confession.json', 'The First Helvetic Confession',
                                               'Basel, 1536 (George Wishart\'s English)', '1st Helv.', R,
                                               notes='Early-modern English spelling of Wishart\'s translation is retained.'),
    'first-basel': lambda: convert_articles('first-basel', 'first_confession_of_basel.json', 'The First Confession of Basel',
                                            'Johannes Oecolampadius and Oswald Myconius, 1534', 'Basel', R),
    'consensus-tigurinus': lambda: convert_articles('consensus-tigurinus', 'consensus_tigurinus.json', 'The Consensus Tigurinus',
                                                    'John Calvin and Heinrich Bullinger, 1549', 'Cons. Tig.', R),
    'ten-theses-berne': lambda: convert_articles('ten-theses-berne', 'ten_theses_of_berne.json', 'The Ten Theses of Berne',
                                                 'Berchtold Haller and Franz Kolb, 1528', 'Berne', R, article_label_name='Thesis'),
    'zwingli-67-articles': lambda: convert_articles('zwingli-67-articles', 'zwinglis_67_articles.json', "Zwingli's Sixty-seven Articles",
                                                    'Ulrich Zwingli, 1523', 'Zwingli 67', R),
    'council-of-orange': lambda: convert_articles('council-of-orange', 'council_of_orange.json', 'The Canons of the Council of Orange',
                                                  'Second Council of Orange, 529', 'Orange', [], article_label_name='Canon'),
    'waldensian-confession': lambda: convert_articles('waldensian-confession', 'waldensian_confession.json', 'The Waldensian Confession',
                                                      'Waldensian, traditionally dated 1120', 'Waldensian', []),
    'abstract-of-principles': lambda: convert_articles('abstract-of-principles', 'abstract_of_principles.json', 'The Abstract of Principles',
                                                       'Basil Manly Jr., Southern Baptist Theological Seminary, 1858', 'Abstract', B),
    # --- catechisms ---
    'westminster-larger': lambda: convert_catechism('westminster-larger', 'westminster_larger_catechism.json', 'The Westminster Larger Catechism',
                                                    'Westminster Assembly, 1647', 'WLC', R),
    'westminster-shorter': lambda: convert_catechism('westminster-shorter', 'westminster_shorter_catechism.json', 'The Westminster Shorter Catechism',
                                                     'Westminster Assembly, 1647', 'WSC', R),
    'keach': lambda: convert_catechism('keach', 'keachs_catechism.json', "Keach's Catechism", 'Benjamin Keach, 1677/1794', 'Keach', B),
    'baptist-catechism-1695': lambda: convert_catechism('baptist-catechism-1695', '1695_baptist_catechism.json', 'The Baptist Catechism (1695)',
                                                        'Particular Baptists, 1695', 'Bapt. Cat.', B),
    'puritan-catechism': lambda: convert_catechism('puritan-catechism', 'puritan_catechism.json', "Spurgeon's Puritan Catechism",
                                                   'C. H. Spurgeon, 1855', 'Puritan Cat.', B),
    'catechism-young-children': lambda: convert_catechism('catechism-young-children', 'catechism_for_young_children.json',
                                                          'Catechism for Young Children', 'Joseph P. Engles, 1840', 'CYC', R),
    'flavel-exposition': lambda: convert_expository_catechism('flavel-exposition', 'exposition_of_the_assemblies_catechism.json',
                                                              "Flavel's Exposition of the Assembly's Catechism", 'John Flavel, 1688', 'Flavel', R,
                                                              notes='Unnumbered continuation sections of the source are folded into the preceding question.'),
    'henry-scripture-catechism': lambda: convert_expository_catechism('henry-scripture-catechism', 'matthew_henrys_scripture_catechism.json',
                                                                      "Matthew Henry's Scripture Catechism", 'Matthew Henry, 1703', 'Henry', R),
    'fisher-catechism-explained': lambda: convert_expository_catechism('fisher-catechism-explained', 'shorter_catechism_explained.json',
                                                                       "The Shorter Catechism Explained", 'James Fisher and Ebenezer Erskine, 1765',
                                                                       'Fisher', R),
    # --- other sources ---
    'luther-small-catechism': convert_luther,
    'baltimore-catechism': convert_baltimore,
    'schleitheim': convert_schleitheim,
    'thirty-nine-articles': convert_thirty_nine_articles,
}


def main(argv):
    ids = argv or list(JOBS)
    for wid in ids:
        JOBS[wid]()
        print('ok', wid)
    print()
    for wid, shelf, fam in DONE:
        print(f'{wid}\t{shelf}\t{fam}')


if __name__ == '__main__':
    main(sys.argv[1:])
