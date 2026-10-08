#!/usr/bin/env node
/* Build script for the Sacred Texts Reader.
   Reads registry.json and works/<work>/..., validates, builds search indexes, and emits:
     dist/reader.html   — one self-contained file (all data inline), the USB/kiosk deliverable
     dist/site/         — split folder for a static web server or file:// (json + .js wrappers)
   Usage: node build.js [--compress] [--only=bundle|site] [--out=dist]
     --compress   deflate each inline block (≈4:1 on scripture text); reader inflates on demand
     --profile=profiles/<name>.json   restrict traditions / works / editions for this build (see profiles/)
     --index      also emit prebuilt search indexes (doubles data size; without them the reader scans unit files, which is fine offline)
*/
'use strict';
const fs = require('fs'), path = require('path'), zlib = require('zlib');

const args = Object.fromEntries(process.argv.slice(2).map(a => { const m = a.match(/^--([\w-]+)(?:=(.*))?$/); return m ? [m[1], m[2] ?? true] : [a, true]; }));
const ROOT = __dirname, OUT = path.join(ROOT, args.out || 'dist');
const COMPRESS = !!args.compress, ONLY = args.only || 'both', INDEX = !!args.index;
/* --profile=profiles/<name>.json : { "traditions": [ids] | null, "exclude": [workIds], "editions": { "<workId>": [editionIds] } }
   Restricts what goes into this build without touching the data: traditions not listed are disabled, excluded works are
   dropped from shelves, and for works listed under "editions" only those editions are emitted (manifest pruned to match). */
const PROFILE = args.profile ? JSON.parse(fs.readFileSync(path.isAbsolute(args.profile) ? args.profile : path.join(ROOT, args.profile), 'utf8')) : null;

const readJSON = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const problems = [];
const warn = (m) => problems.push(m);

/* ---------- 1. Load & validate ---------- */
const registry = readJSON(path.join(ROOT, 'registry.json'));
if (PROFILE) {
  for (const t of registry.traditions) {
    if (PROFILE.traditions && !PROFILE.traditions.includes(t.id)) t.enabled = false;
    if (!t.enabled) continue;
    for (const k of Object.keys(t.shelves || {})) t.shelves[k] = t.shelves[k].filter(id => !(PROFILE.exclude || []).includes(id));
  }
  registry.deployment = PROFILE.name || path.basename(args.profile, '.json');
}
const workIds = new Set();
const VALIDATE_ONLY = args['validate-work'] ? String(args['validate-work']).split(',') : null;
if (VALIDATE_ONLY) VALIDATE_ONLY.forEach(id => workIds.add(id));
else for (const t of registry.traditions) if (t.enabled) for (const [shelf, ids] of Object.entries(t.shelves || {})) for (const id of ids) workIds.add(id);

const works = new Map();   // workId -> { manifest, units: Map<path, obj> }
for (const id of workIds) {
  const dir = path.join(ROOT, 'works', id);
  const mp = path.join(dir, 'manifest.json');
  if (!fs.existsSync(mp)) { warn(`work "${id}" is on a shelf but works/${id}/manifest.json is missing`); continue; }
  const m = readJSON(mp);
  if (PROFILE?.editions?.[id]) {
    const keep = PROFILE.editions[id];
    m.editions = m.editions.filter(e => keep.includes(e.id));
    if (!m.editions.length) warn(`${id}: profile keeps no editions`);
    m.defaultEditions = (m.defaultEditions || []).filter(e => keep.includes(e));
    if (!m.defaultEditions.length) m.defaultEditions = [m.editions[0]?.id].filter(Boolean);
  }
  if (m.workId !== id) warn(`works/${id}/manifest.json has workId "${m.workId}"`);
  if (!m.levels?.some(l => l.isUnit)) warn(`${id}: no level has isUnit: true`);
  const units = new Map();
  for (const ed of m.editions || []) {
    if (!ed.direction) warn(`${id}/${ed.id}: edition has no direction`);
    const edir = path.join(dir, ed.id);
    if (!fs.existsSync(edir)) { warn(`${id}/${ed.id}: folder missing`); continue; }
    const files = fs.readdirSync(edir).filter(f => f.endsWith('.json')).sort();
    if (!files.length) warn(`${id}/${ed.id}: no unit files`);
    const found = [];
    for (const f of files) {
      const u = readJSON(path.join(edir, f));
      const unitFromName = f.replace(/\.json$/, '');
      if (u.unit.replace(/:/g, '-') !== unitFromName) warn(`${id}/${ed.id}/${f}: file name does not match unit "${u.unit}"`);
      if (u.editionId !== ed.id || u.workId !== id) warn(`${id}/${ed.id}/${f}: workId/editionId mismatch`);
      for (const p of u.passages || []) if (!p.ref.startsWith(u.unit + ':') && p.ref !== u.unit) warn(`${id}/${ed.id}/${f}: passage ref "${p.ref}" is outside unit "${u.unit}"`);
      units.set(`works/${id}/${ed.id}/${unitFromName}`, u);
      found.push(u.unit);
    }
    if (ed.available) for (const a of ed.available) if (!found.includes(a)) warn(`${id}/${ed.id}: "available" lists ${a} but no file for it`);
  }
  works.set(id, { manifest: m, units });
  if (VALIDATE_ONLY) {
    let passages = 0; for (const u of units.values()) passages += (u.passages || []).length;
    const HTML = /<\/?[a-z][^>]*>/i; let html = 0, nonNfc = 0;
    for (const u of units.values()) for (const p of u.passages || []) { if (HTML.test(p.text) || HTML.test(p.heading || '')) html++; if (p.text !== p.text.normalize('NFC')) nonNfc++; }
    if (html) warn(`${id}: ${html} passage(s) contain HTML tags`);
    if (nonNfc) warn(`${id}: ${nonNfc} passage(s) not NFC-normalized`);
    console.log(`${id}: ${m.editions.length} edition(s), ${units.size} unit file(s), ${passages} passages`);
  }
}
if (VALIDATE_ONLY) { if (problems.length) { console.error('Validation:'); for (const p of problems) console.error('  - ' + p); } process.exit(problems.some(p => /missing|mismatch|outside|HTML/.test(p)) ? 1 : 0); }
if (problems.length) { console.error('Validation:'); for (const p of problems) console.error('  - ' + p); }
const fatal = problems.filter(p => /missing|mismatch|outside/.test(p));
if (fatal.length) { console.error(`\n${fatal.length} fatal problem(s); not building.`); process.exit(1); }

/* ---------- 2. Search indexes (one per edition) ---------- */
const indexes = new Map(); // path -> {refs, text}
for (const [id, w] of works) {
  for (const ed of w.manifest.editions || []) {
    const refs = [], text = [];
    const prefix = `works/${id}/${ed.id}/`;
    const keys = [...w.units.keys()].filter(k => k.startsWith(prefix)).sort(naturalUnitOrder(w.manifest, ed));
    for (const k of keys) for (const p of w.units.get(k).passages) { refs.push(p.ref); text.push(stripMarkup(p.text)); }
    indexes.set(`search/${id}/${ed.id}`, { refs, text });
  }
}
function stripMarkup(t) { return t.replace(/\[\[(.+?)\]\]/g, '$1').replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1').replace(/(^|[\s(])_(.+?)_/g, '$1$2'); }
function naturalUnitOrder(m, ed) {
  let order = null;
  if (m.canons && m.books) { order = []; for (const b of (m.canons[ed.canon] || Object.keys(m.books))) for (let c = 1; c <= (m.chapters[b] || 1); c++) order.push(`${b}-${c}`); }
  else if (m.toc) { order = []; for (const t of m.toc) { if (t.children) t.children.forEach(c => order.push(c.ref.replace(/:/g, '-'))); else order.push(t.ref.replace(/:/g, '-')); } }
  return (a, b) => { if (!order) return a.localeCompare(b, undefined, { numeric: true }); const ua = a.split('/').pop(), ub = b.split('/').pop(); return order.indexOf(ua) - order.indexOf(ub); };
}

/* ---------- 3. Collect everything to emit ---------- */
const data = new Map();     // path (no extension) -> object
data.set('registry', registry);
for (const [id, w] of works) { data.set(`works/${id}/manifest`, w.manifest); for (const [k, v] of w.units) data.set(k, v); }
if (INDEX) for (const [k, v] of indexes) data.set(k, v);   // --index: prebuilt per-edition search index (doubles data size; the reader scans units when absent)

const src = f => fs.readFileSync(path.join(ROOT, 'src', f), 'utf8');
const html = src('index.html'), css = src('app.css'), js = src('app.js');
fs.mkdirSync(OUT, { recursive: true });

/* ---------- 4a. Split site ---------- */
if (ONLY !== 'bundle') {
  const site = path.join(OUT, 'site');
  fs.rmSync(site, { recursive: true, force: true }); fs.mkdirSync(site, { recursive: true });
  fs.writeFileSync(path.join(site, 'index.html'), html);
  fs.writeFileSync(path.join(site, 'app.css'), css);
  fs.writeFileSync(path.join(site, 'app.js'), js);
  for (const [p, obj] of data) {
    const fp = path.join(site, p); fs.mkdirSync(path.dirname(fp), { recursive: true });
    const json = JSON.stringify(obj);
    fs.writeFileSync(fp + '.json', json);
    fs.writeFileSync(fp + '.js', `window.__lib.deliver(${JSON.stringify(p)},${json});`);
  }
  console.log(`site:   ${site} (${data.size} data files, each as .json and .js)`);
}

/* ---------- 4b. Single-file bundle (streamed; data grouped into ~2 MB chunk blocks so the DOM stays small) ---------- */
if (ONLY !== 'site') {
  const fp = path.join(OUT, 'reader.html');
  const head = html.replace(/<!--BUILD:CSS-->[\s\S]*?<!--\/BUILD:CSS-->/, `<style>\n${css}\n</style>`);
  const [before, afterData] = head.split(/<!--BUILD:DATA-->[\s\S]*?<!--\/BUILD:DATA-->/);
  const tail = afterData.replace(/<!--BUILD:JS-->[\s\S]*?<!--\/BUILD:JS-->/, `<script>\n${js.replace(/<\/script/gi, '<\\/script')}\n</script>`);
  const fd = fs.openSync(fp, 'w');
  fs.writeSync(fd, before);
  const CHUNK = 2 * 1024 * 1024;
  const index = {};               // path -> chunk number
  let chunkNo = 0, chunk = [], chunkBytes = 0, rawBytes = 0, outBytes = 0;
  const flush = () => {
    if (!chunk.length) return;
    // a chunk is a JSON object { path: body }; body is deflate-raw+base64 (or plain JSON text) per entry
    const body = '{' + chunk.join(',') + '}';
    fs.writeSync(fd, `<script type="text/plain" data-chunk="${chunkNo}"${COMPRESS ? ' data-enc="deflate-raw-b64"' : ''}>`);
    fs.writeSync(fd, body.replace(/<\/(script)/gi, '<\\/$1')); fs.writeSync(fd, '</script>\n');
    outBytes += body.length; chunkNo++; chunk = []; chunkBytes = 0;
  };
  for (const [p, obj] of data) {
    const json = JSON.stringify(obj); rawBytes += Buffer.byteLength(json);
    const body = COMPRESS ? zlib.deflateRawSync(Buffer.from(json), { level: 9 }).toString('base64') : json;
    index[p] = chunkNo;
    chunk.push(JSON.stringify(p) + ':' + JSON.stringify(body)); chunkBytes += body.length;
    if (chunkBytes >= CHUNK) flush();
  }
  flush();
  fs.writeSync(fd, `<script type="text/plain" data-index="1">${JSON.stringify(index)}</script>\n`);
  fs.writeSync(fd, tail); fs.closeSync(fd);
  const mb = n => (n / 1048576).toFixed(1) + ' MB';
  console.log(`bundle: ${fp} — ${mb(fs.statSync(fp).size)} total; data ${mb(rawBytes)} raw → ${mb(outBytes)} embedded${COMPRESS ? ' (compressed)' : ''}; ${data.size} files in ${chunkNo} chunks`);
}
if (problems.length) console.log(`${problems.length} warning(s) above.`);
