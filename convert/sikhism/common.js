/* Shared helpers for the Sikh text converters (shabados/database tag 4.8.7).
   Source files are untrusted data: they are only ever parsed with JSON.parse. */
'use strict';
const fs = require('fs'), path = require('path');
const g = require('gurmukhi-utils');

const HERE = __dirname;
const READER = path.resolve(HERE, '..', '..');
const WORKS = path.join(READER, 'works');
const SOURCES = process.env.SIKH_SOURCES ||
  '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/sikhism/db487/data';
const REPO = 'https://github.com/shabados/database/tree/4.8.7/data';
const TRAD = 'sikhism';

const PA_EDITION = { lang: 'pa', script: 'Guru', direction: 'ltr', font: 'gurmukhi' };
const EN_EDITION = { lang: 'en', script: 'Latn', direction: 'ltr' };

const readJSON = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const slugOk = s => /^[a-z0-9-]+$/.test(s);
const HTML = /<\/?[a-zA-Z][^>]*>/;

/* NFC, collapse spaces, trim; keep \n. */
function norm(t) {
  if (t == null) return '';
  t = String(t).normalize('NFC').replace(/ /g, ' ').replace(/\r\n?/g, '\n');
  t = t.replace(/[ \t​﻿]+/g, ' ');
  t = t.split('\n').map(l => l.trim()).join('\n').replace(/\n{2,}/g, '\n');
  t = t.replace(/ ([,.;:!?])/g, '$1').replace(/\( +/g, '(').replace(/ +\)/g, ')');
  return t.trim();
}

/* ASCII (Gurbani Akhar / shabados font encoding) → Unicode Gurmukhi, vishraam marks removed. */
function gurmukhi(ascii) {
  if (!ascii) return '';
  let t = g.toUnicode(g.stripVishraams(String(ascii)));
  return norm(t);
}

/* Load one source ("Sri Guru Granth Sahib Ji", "Sri Dasam Granth", "Ardaas") as an ordered
   array of lines; each line gets .shabad (the containing shabad), .seq (global order) and .first
   (true for the first line of its shabad). */
function loadSource(name) {
  const dir = path.join(SOURCES, name);
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort();
  const lines = [];
  for (const f of files) {
    const shabads = readJSON(path.join(dir, f));
    for (const sh of shabads) {
      sh.lines.forEach((l, i) => {
        l.shabad = sh; l.first = i === 0; l.seq = lines.length; l.sourceName = name;
        lines.push(l);
      });
    }
  }
  return lines;
}

function translation(line, lang, source) {
  const t = line.translations?.[lang]?.[source]?.translation;
  return norm(t);
}

/* ---------- output ---------- */
function resetWork(workId) {
  const d = path.join(WORKS, workId);
  fs.rmSync(d, { recursive: true, force: true });
  fs.mkdirSync(d, { recursive: true });
  return d;
}

function writeUnit(workId, editionId, unit, passages) {
  if (!passages.length) throw new Error(`${workId}/${editionId}/${unit}: no passages`);
  for (const seg of unit.split(':')) if (!slugOk(seg)) throw new Error(`${workId}: bad unit ${unit}`);
  for (const p of passages) {
    if (!p.text) throw new Error(`${workId}/${editionId}/${unit}: empty passage ${p.ref}`);
    if (!(p.ref === unit || p.ref.startsWith(unit + ':'))) throw new Error(`${workId}: ${p.ref} outside ${unit}`);
    for (const seg of p.ref.split(':')) if (!slugOk(seg)) throw new Error(`${workId}: bad ref ${p.ref}`);
    if (HTML.test(p.text)) throw new Error(`${workId}: html in ${p.ref}`);
    p.text = p.text.normalize('NFC');
    if (p.heading != null) { if (!p.heading) delete p.heading; else p.heading = p.heading.normalize('NFC'); }
  }
  const d = path.join(WORKS, workId, editionId);
  fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, unit.replace(/:/g, '-') + '.json'),
    JSON.stringify({ workId, editionId: editionId, unit, passages }) + '\n');
}

function writeManifest(workId, m) {
  if (m.workId !== workId) throw new Error('workId mismatch');
  if (!m.levels.some(l => l.isUnit)) throw new Error('no unit level');
  for (const ed of m.editions) if (!(slugOk(ed.id) && ed.license && ed.source && ed.direction)) throw new Error(`bad edition ${ed.id}`);
  for (const t of m.toc || []) {
    for (const seg of t.ref.split(':')) if (!slugOk(seg)) throw new Error(`bad toc ref ${t.ref}`);
    for (const c of t.children || []) for (const seg of c.ref.split(':')) if (!slugOk(seg)) throw new Error(`bad toc ref ${c.ref}`);
  }
  fs.writeFileSync(path.join(WORKS, workId, 'manifest.json'), JSON.stringify(m, null, 1) + '\n');
}

function edition(id, label, role, license, source, base, extra) {
  return Object.assign({ id }, base, { label: { en: label }, role, license, source }, extra || {});
}

module.exports = { READER, WORKS, SOURCES, REPO, TRAD, PA_EDITION, EN_EDITION, readJSON, norm, gurmukhi, loadSource,
  translation, resetWork, writeUnit, writeManifest, edition, g };
