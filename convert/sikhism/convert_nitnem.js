#!/usr/bin/env node
/* Nitnem (daily banis) → works/nitnem, from shabados/database 4.8.7 data/banis.json.
   Each bani is one unit; its line ranges are resolved by line id across the Sri Guru Granth Sahib Ji,
   Sri Dasam Granth and Ardaas data. Refs <bani>:<n> (n = running line number inside the bani). */
'use strict';
const path = require('path');
const C = require('./common');

const WORK = 'nitnem';
const SRC_NAMES = ['Sri Guru Granth Sahib Ji', 'Sri Dasam Granth', 'Ardaas'];
const byId = new Map(), seqs = {};
for (const s of SRC_NAMES) { seqs[s] = C.loadSource(s); for (const l of seqs[s]) byId.set(l.id, l); }
const banis = C.readJSON(path.join(C.SOURCES, 'banis.json'));
const sources = C.readJSON(path.join(C.SOURCES, 'sources.json'));
const writers = C.readJSON(path.join(C.SOURCES, 'writers.json'));
const sectionPa = {}; for (const s of sources) for (const sec of s.sections || []) sectionPa[sec.name_english] = C.gurmukhi(sec.name_gurmukhi);
const writerPa = {}; for (const w of writers) writerPa[w.name_english] = C.gurmukhi(w.name_gurmukhi);

/* slug, source bani name, labels, aliases */
const BANIS = [
  ['japji-sahib', 'Jap Ji Sahib', 'Japji Sahib', ['japji', 'jap ji', 'japji sahib', 'jap ji sahib', 'japu', 'jap']],
  ['jaap-sahib', 'Jaap Sahib', 'Jaap Sahib', ['jaap', 'jaap sahib', 'japu sahib']],
  ['tav-prasad-savaiye', 'Tav Prasad Savaiye (Sravag Sudh)', 'Tav-Prasad Savaiye', ['tav prasad savaiye', 'tav-prasad savaiye', 'savaiye', 'swaiye', 'sravag sudh']],
  ['chaupai-sahib', 'Benti Chaupai Sahib', 'Chaupai Sahib', ['chaupai', 'chaupai sahib', 'benti chaupai', 'kabyo bach benti chaupai']],
  ['anand-sahib', 'Anand Sahib', 'Anand Sahib', ['anand', 'anand sahib', 'anandu sahib']],
  ['rehras-sahib', 'Rehras Sahib (S.)', 'Rehras Sahib', ['rehras', 'rehras sahib', 'rehraas', 'rehiras', 'so dar', 'evening prayer']],
  ['kirtan-sohila', 'Sohila Sahib', 'Kirtan Sohila', ['sohila', 'kirtan sohila', 'sohila sahib', 'night prayer']],
  ['sukhmani-sahib', 'Sukhmani Sahib', 'Sukhmani Sahib', ['sukhmani', 'sukhmani sahib']],
  ['asa-ki-var', 'Asa Ki Var', 'Asa Ki Var', ['asa ki var', 'asa di var', 'aasa ki vaar', 'asa ki vaar']],
  ['ardaas', 'Ardaas', 'Ardaas', ['ardaas', 'ardas']],
];

function english(l) {
  const en = l.translations?.English || {};
  for (const name of ['Dr. Sant Singh Khalsa', 'Dr. Surinder Singh Kohli', 'SGPC']) if (en[name]) return C.norm(en[name].translation);
  for (const v of Object.values(en)) if (v.translation) return C.norm(v.translation);
  return '';
}
function headingEn(sh) { return sh.writer === 'SGPC' ? sh.section : `${sh.section} — ${sh.writer}`; }
function headingPa(sh) { const s = sectionPa[sh.section] || sh.section; return sh.writer === 'SGPC' ? s : `${s} — ${writerPa[sh.writer] || sh.writer}`; }

C.resetWork(WORK);
const toc = [], aliases = {}; let total = { pa: 0, 'en-khalsa': 0 };
for (const [slug, srcName, label, al] of BANIS) {
  const b = banis.find(x => x.name_english === srcName);
  if (!b) { console.log(`skip ${slug}: not in banis.json`); continue; }
  const lines = [];
  for (const r of b.lines) {
    const a = byId.get(r.start_line), z = byId.get(r.end_line);
    if (!a || !z || a.sourceName !== z.sourceName || z.seq < a.seq) throw new Error(`${slug}: bad range ${JSON.stringify(r)}`);
    lines.push(...seqs[a.sourceName].slice(a.seq, z.seq + 1));
  }
  const pa = [], en = [];
  let prevShabad = null;
  lines.forEach((l, i) => {
    const ref = `${slug}:${i + 1}`;
    const newShabad = !prevShabad || l.shabad.section !== prevShabad.section || l.shabad.writer !== prevShabad.writer; prevShabad = l.shabad;
    const t = C.gurmukhi(l.gurmukhi);
    if (t) { const p = { ref, text: t }; if (newShabad) p.heading = headingPa(l.shabad); pa.push(p); }
    const e = english(l);
    if (e) { const p = { ref, text: e }; if (newShabad) p.heading = headingEn(l.shabad); en.push(p); }
  });
  C.writeUnit(WORK, 'pa', slug, pa); C.writeUnit(WORK, 'en-khalsa', slug, en);
  total.pa += pa.length; total['en-khalsa'] += en.length;
  toc.push({ ref: slug, label: { en: label, pa: C.gurmukhi(b.name_gurmukhi) }, count: lines.length });
  aliases[slug] = al;
}

const LICENSE = 'Public Domain Mark per shabados/database; translations as attributed';
const manifest = {
  schemaVersion: 1, workId: WORK, tradition: C.TRAD, shelf: 'devotional', families: [],
  title: { en: 'Nitnem', pa: 'ਨਿਤਨੇਮ' },
  subtitle: { en: 'The daily prayers of the Sikhs: Japji, Jaap, Tav-Prasad Savaiye, Chaupai, Anand, Rehras, Kirtan Sohila, with Sukhmani Sahib, Asa Ki Var and Ardaas' },
  levels: [{ id: 'bani', label: { en: 'Bani' }, isUnit: true }, { id: 'line', label: { en: 'Line' } }],
  citation: { format: '{work} {bani} {line}', rangeFormat: '{work} {bani} {line}–{line2}', workAbbrev: { en: 'Nitnem' } },
  toc,
  editions: [
    C.edition('pa', 'Gurmukhi', 'original', LICENSE, `${C.REPO}/banis.json`, C.PA_EDITION,
      { notes: { en: 'Gurmukhi text converted from the shabados ASCII font encoding; vishraam marks not shown. Rehras Sahib follows the SGPC (shorter) order in banis.json.' } }),
    C.edition('en-khalsa', 'English (Sant Singh Khalsa; Dasam Granth banis: Surinder Singh Kohli)', 'translation', LICENSE, `${C.REPO}/banis.json`, C.EN_EDITION,
      { notes: { en: 'Lines from Sri Guru Granth Sahib Ji are in Dr. Sant Singh Khalsa’s translation; lines from Sri Dasam Granth (Jaap Sahib, Tav-Prasad Savaiye, Chaupai Sahib, the opening of Ardaas) are in Dr. Surinder Singh Kohli’s; the Ardaas text is the SGPC English.' } }),
  ],
  defaultEditions: ['pa', 'en-khalsa'],
  aliases,
  notes: { en: 'The Sikh daily prayers, in the traditional order of the Nitnem gutka; each bani is shown as one continuous text with its source lines.' },
};
C.writeManifest(WORK, manifest);
console.log(`${WORK}: units=${toc.length} passages=${JSON.stringify(total)}`);
