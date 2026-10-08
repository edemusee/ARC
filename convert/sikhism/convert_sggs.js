#!/usr/bin/env node
/* Sri Guru Granth Sahib Ji → works/guru-granth-sahib (shabados/database 4.8.7).
   Units = Ang 1…1430; refs <ang>:<source_line>, with a -2, -3… suffix when several panktis share one
   physical line of the Damdami Bir. Editions: pa (Gurmukhi Unicode), en-khalsa, en-manmohan, pa-manmohan. */
'use strict';
const path = require('path');
const C = require('./common');

const WORK = 'guru-granth-sahib';
const lines = C.loadSource('Sri Guru Granth Sahib Ji');
const sources = C.readJSON(path.join(C.SOURCES, 'sources.json'));
const writers = C.readJSON(path.join(C.SOURCES, 'writers.json'));
const sggsSrc = sources.find(s => s.name_english === 'Sri Guru Granth Sahib Ji');
const sectionPa = {}; for (const s of sggsSrc.sections) sectionPa[s.name_english] = C.gurmukhi(s.name_gurmukhi);
const writerPa = {}; for (const w of writers) writerPa[w.name_english] = C.gurmukhi(w.name_gurmukhi);

/* Assign page + ref to every line, in sequence order. */
const pages = new Map(); // page -> lines
let curPage = 0, prevLine = 0;
for (const l of lines) {
  let p = l.source_page;
  if (!l.first && p === curPage && l.source_line < prevLine - 10) p = curPage + 1; // mislabelled page break
  if (p < curPage) p = curPage;
  curPage = p; prevLine = l.source_line;
  l.page = p;
  if (!pages.has(p)) pages.set(p, []);
  pages.get(p).push(l);
}
for (const [p, ls] of pages) {
  const seen = new Map();
  for (const l of ls) {
    const n = (seen.get(l.source_line) || 0) + 1; seen.set(l.source_line, n);
    l.ref = `${p}:${l.source_line}${n > 1 ? '-' + n : ''}`;
  }
}
if (pages.size !== 1430) throw new Error(`expected 1430 pages, got ${pages.size}`);

const EDITIONS = [
  { id: 'pa', text: l => C.gurmukhi(l.gurmukhi), heading: sh => `${sectionPa[sh.section] || sh.section} — ${writerPa[sh.writer] || sh.writer}` },
  { id: 'en-khalsa', text: l => C.translation(l, 'English', 'Dr. Sant Singh Khalsa'), heading: sh => `${sh.section} — ${sh.writer}` },
  { id: 'en-manmohan', text: l => C.translation(l, 'English', 'Bhai Manmohan Singh'), heading: sh => `${sh.section} — ${sh.writer}` },
  { id: 'pa-manmohan', text: l => C.norm(C.translation(l, 'Punjabi', 'Bhai Manmohan Singh')), heading: sh => `${sectionPa[sh.section] || sh.section} — ${writerPa[sh.writer] || sh.writer}` },
];

C.resetWork(WORK);
const counts = {};
for (const ed of EDITIONS) {
  let n = 0;
  for (const [p, ls] of pages) {
    const passages = [];
    for (const l of ls) {
      const text = ed.text(l);
      if (!text) continue;
      const ps = { ref: l.ref, text };
      if (l.first) ps.heading = ed.heading(l.shabad);
      passages.push(ps);
    }
    if (passages.length) { C.writeUnit(WORK, ed.id, String(p), passages); n += passages.length; }
  }
  counts[ed.id] = n;
}

/* toc + aliases */
const toc = [], aliases = {};
for (const [p, ls] of pages) {
  const sec = ls[0].shabad.section;
  toc.push({ ref: String(p), label: { en: `Ang ${p} · ${sec}`, pa: `ਅੰਗ ${C.g.toUnicode(String(p))} · ${sectionPa[sec] || sec}` }, count: ls.length });
  aliases[String(p)] = [`ang ${p}`, `page ${p}`, `sggs ${p}`];
}

const LICENSE = 'Public Domain Mark per shabados/database; translations as attributed';
const src = (sub) => `${C.REPO}/${sub}`;
const manifest = {
  schemaVersion: 1, workId: WORK, tradition: C.TRAD, shelf: 'scripture', families: [],
  title: { en: 'Sri Guru Granth Sahib Ji', pa: 'ਸ੍ਰੀ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ' },
  subtitle: { en: 'The eternal Guru of the Sikhs — 1430 Angs' },
  levels: [{ id: 'ang', label: { en: 'Ang', pa: 'ਅੰਗ' }, isUnit: true }, { id: 'line', label: { en: 'Line' } }],
  citation: { format: '{work} {ang}:{line}', rangeFormat: '{work} {ang}:{line}–{line2}', workAbbrev: { en: 'SGGS' } },
  toc,
  editions: [
    C.edition('pa', 'Gurmukhi', 'original', LICENSE, src('Sri%20Guru%20Granth%20Sahib%20Ji'), C.PA_EDITION,
      { notes: { en: 'Gurmukhi text of the Sri Damdami Bir, converted from the shabados ASCII font encoding; vishraam (pause) marks are not shown. Headings give the raag/section and the writer of each shabad.' } }),
    C.edition('en-khalsa', 'English (Sant Singh Khalsa)', 'translation', LICENSE, src('Sri%20Guru%20Granth%20Sahib%20Ji'), C.EN_EDITION,
      { notes: { en: 'Translation by Dr. Sant Singh Khalsa, as carried in shabados/database.' } }),
    C.edition('en-manmohan', 'English (Bhai Manmohan Singh)', 'translation', LICENSE, src('Sri%20Guru%20Granth%20Sahib%20Ji'), C.EN_EDITION,
      { notes: { en: 'Translation by Bhai Manmohan Singh (SGPC), as carried in shabados/database.' } }),
    C.edition('pa-manmohan', 'Punjabi gloss (Bhai Manmohan Singh)', 'gloss', LICENSE, src('Sri%20Guru%20Granth%20Sahib%20Ji'), C.PA_EDITION,
      { notes: { en: 'Punjabi prose rendering by Bhai Manmohan Singh (SGPC), as carried in shabados/database.' } }),
  ],
  defaultEditions: ['pa', 'en-khalsa'],
  aliases,
  notes: { en: 'Sri Guru Granth Sahib Ji. Shown by Ang (page) and line as in the Sri Damdami Bir.' },
  previewPolicy: 'reference-only',
};
C.writeManifest(WORK, manifest);
console.log(`${WORK}: units=${pages.size} lines=${lines.length} passages per edition=${JSON.stringify(counts)}`);
