/* ARC — Agency Religious Codex — generic reader driven by registry.json and per-work manifests.
   No framework, no build-time dependencies. Works from a single bundled file (inline data blocks),
   from a folder opened via file:// (.js unit wrappers), or from a static web server (.json). */
(() => {
'use strict';

/* ---------------- Loader: inline block → file:// script → fetch ---------------- */
const Lib = (() => {
  const cache = new Map();          // path -> Promise<object>
  const pending = new Map();
  const isFile = location.protocol === 'file:';
  window.__lib = { deliver(path, obj) { const p = pending.get(path); if (p) { p(obj); pending.delete(path); } else cache.set(path, Promise.resolve(obj)); } };

  // Bundle layout: an index block (path -> chunk number) plus ~2 MB chunk blocks, each a JSON object { path: body }.
  // Older bundles used one block per path; both are supported.
  const indexEl = document.querySelector('script[type="text/plain"][data-index]');
  const index = indexEl ? JSON.parse(indexEl.textContent) : null;
  const chunks = new Map();         // chunk number -> parsed { path: body }
  const perPath = new Map();
  if (!index) for (const el of document.querySelectorAll('script[type="text/plain"][data-path]')) perPath.set(el.dataset.path, el);
  const inBundle = index ? Object.keys(index).length > 0 : perPath.size > 0;

  async function inflate(body, enc) {
    if (!enc) return JSON.parse(body);
    if (enc === 'deflate-raw-b64') {
      const bytes = Uint8Array.from(atob(body.replace(/\s+/g, '')), c => c.charCodeAt(0));
      const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
      return JSON.parse(await new Response(stream).text());
    }
    throw new Error('Unknown encoding ' + enc);
  }
  function chunkBodies(n) {
    if (!chunks.has(n)) {
      const el = document.querySelector(`script[type="text/plain"][data-chunk="${n}"]`);
      chunks.set(n, { enc: el.dataset.enc, map: JSON.parse(el.textContent) });
    }
    return chunks.get(n);
  }
  async function fromBundle(path) {
    if (index) { if (!(path in index)) throw new Error('Not in bundle: ' + path); const c = chunkBodies(index[path]); return inflate(c.map[path], c.enc); }
    const el = perPath.get(path); if (!el) throw new Error('Not in bundle: ' + path);
    return inflate(el.textContent, el.dataset.enc);
  }
  function load(path) {
    if (cache.has(path)) return cache.get(path);
    let p;
    if (inBundle) p = fromBundle(path);
    else if (isFile) p = new Promise((resolve, reject) => {
      pending.set(path, resolve);
      const s = document.createElement('script');
      s.src = path + '.js';
      s.onerror = () => { pending.delete(path); reject(new Error('Missing ' + path)); };
      document.head.appendChild(s);
    });
    else p = fetch(path + '.json').then(r => { if (!r.ok) throw new Error('Missing ' + path); return r.json(); });
    cache.set(path, p);
    p.catch(() => cache.delete(path));
    return p;
  }
  return { load, mode: inBundle ? 'bundle' : isFile ? 'file' : 'http' };
})();

/* ---------------- Helpers ---------------- */
const $ = s => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') n.className = v; else if (k === 'text') n.textContent = v; else if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null) n.append(k.nodeType ? k : document.createTextNode(k));
  return n;
};
const L = (obj, lang = 'en') => obj == null ? '' : typeof obj === 'string' ? obj : (obj[lang] ?? Object.values(obj)[0] ?? '');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function renderMarkup(text) {
  return esc(text)
    .replace(/\[\[(.+?)\]\]/g, '<span class="supplied">$1</span>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/(^|[\s(])_(.+?)_(?=[\s.,;:!?)]|$)/g, '$1<span class="smcaps">$2</span>');
}
const unitPath = (work, ed, unit) => `works/${work}/${ed}/${unit.replace(/:/g, '-')}`;

/* Text normalization for search: strips vowel points and accents, folds letter variants.
   Returns the folded string and a map from folded index → original index. */
const ARABIC_FOLD = { 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه', 'ؤ': 'و', 'ئ': 'ي' };
const HEBREW_FINAL = { 'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ' };
const MARK = /\p{M}/u;
function fold(text) {
  let out = '', map = [];
  let i = 0;
  for (const ch of text) {
    const cp = ch.codePointAt(0);
    if (ch === 'ـ' || MARK.test(ch)) { i += ch.length; continue; }           // tatweel, combining marks
    let base = ch.normalize('NFD');
    base = [...base].filter(c => !MARK.test(c)).join('') || '';
    if (base) {
      base = base.toLowerCase();
      base = ARABIC_FOLD[base] ?? HEBREW_FINAL[base] ?? base;
      for (const b of base) { out += b; map.push(i); }
    }
    i += ch.length;
  }
  map.push(text.length);
  return { s: out, map };
}

/* ---------------- State ---------------- */
const S = {
  registry: null, manifests: new Map(), units: new Map(),
  tradition: null, family: '', work: null, unit: null, editions: [], docs: new Map(),
  settings: Object.assign({ theme: 'light', font: 'serif', size: 19, leading: 1.7, layout: 'columns', numbers: true, footnotes: false },
    JSON.parse(localStorage.getItem('reader:settings') || '{}'))
};
try { S.settings = Object.assign(S.settings, JSON.parse(localStorage.getItem('reader:settings') || '{}')); } catch {}

async function manifest(workId) {
  if (!S.manifests.has(workId)) S.manifests.set(workId, await Lib.load(`works/${workId}/manifest`));
  return S.manifests.get(workId);
}
const traditionOf = id => S.registry.traditions.find(t => t.id === id);

/* ---------------- Work structure helpers ---------------- */
function isBibleLike(m) { return !!(m.canons && m.books); }
function editionUnits(m, ed) {
  if (isBibleLike(m)) {
    const books = m.canons[ed.canon] || Object.keys(m.books);
    const list = [];
    for (const b of books) for (let c = 1; c <= (m.chapters[b] || 1); c++) list.push(`${b}:${c}`);
    return list;
  }
  const list = [];
  for (const t of m.toc || []) { if (t.children) for (const c of t.children) list.push(c.ref); else list.push(t.ref); }
  return list;
}
function unitAvailable(ed, unit) { return !ed.available || ed.available.includes(unit); }
function unitLabel(m, unit) {
  if (isBibleLike(m)) { const [b, c] = unit.split(':'); return `${L(m.books[b])} ${c}`; }
  for (const t of m.toc || []) {
    if (t.ref === unit) return L(t.label);
    for (const c of t.children || []) if (c.ref === unit) return `${L(t.label)} ${L(c.label)}`;
  }
  return unit;
}
function cite(m, ref) {
  const segs = ref.split(':');
  const vals = {};
  m.levels.forEach((lv, i) => { vals[lv.id] = segs[i] ?? ''; });
  if (isBibleLike(m)) vals.book = L(m.books[segs[0]]);
  vals.work = L(m.citation.workAbbrev) || L(m.title);
  return m.citation.format.replace(/\{(\w+)\}/g, (_, k) => vals[k] ?? '').replace(/\s+/g, ' ').trim();
}
function familyRank(tagged, fam) {
  const f = tagged || [];
  if (!fam) return f.length ? 1 : 0;
  return f.includes(fam) ? 0 : f.length ? 2 : 1;
}
function sortedEditions(m) {
  return [...m.editions].sort((a, b) => familyRank(a.families, S.family) - familyRank(b.families, S.family));
}

/* Parse a typed reference against the open work. Returns {unit, ref} or null. */
function parseRef(m, input) {
  let s = input.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.,]/g, ':').replace(/\s*:\s*/g, ':').replace(/\s*-\s*/g, '-');
  if (!s) return null;
  const names = [];
  const add = (code, label) => { if (label) names.push([String(label).toLowerCase().replace(/\s+/g, ' '), String(code)]); };
  if (isBibleLike(m)) for (const [code, lab] of Object.entries(m.books)) { add(code, code); for (const v of Object.values(lab)) add(code, v); }
  for (const t of m.toc || []) {
    add(t.ref, t.ref); for (const v of Object.values(t.label || {})) add(t.ref, v);
    for (const c of t.children || []) { add(c.ref, c.ref); for (const v of Object.values(c.label || {})) add(c.ref, `${L(t.label)} ${v}`); }
  }
  for (const [code, list] of Object.entries(m.aliases || {})) for (const a of list) add(code, a);
  names.sort((a, b) => b[0].length - a[0].length);
  let top = null, rest = s;
  for (const [name, code] of names) {
    if (s === name || s.startsWith(name + ' ') || s.startsWith(name + ':')) { top = code; rest = s.slice(name.length).trim().replace(/^:/, ''); break; }
  }
  // tokens: numbers, talmud-style "2a" → 2, a; keep "402-2" style compound tokens whole
  const nums = [];
  for (const tok of (rest ? rest.split(/[:\s]+/).filter(Boolean) : [])) { const t = tok.match(/^(\d+)([ab])$/); if (t) nums.push(t[1], t[2]); else nums.push(tok); }
  if (!top && !nums.length) return null;
  const depth = m.levels.length, unitDepth = m.levels.findIndex(l => l.isUnit) + 1;
  const current = S.unit ? S.unit.split(':') : [];
  let segs;
  if (top) segs = top.split(':').concat(nums);
  else { const ctx = Math.max(0, Math.min(current.length, depth - nums.length)); segs = current.slice(0, ctx).concat(nums); }
  segs = segs.slice(0, depth);
  while (segs.length < unitDepth) segs.push('1');
  const unit = segs.slice(0, unitDepth).join(':');
  const ed = primaryEdition();
  if (ed && !editionUnits(m, ed).includes(unit)) {
    // a unit-level alias may point straight at a unit (e.g. toc child refs); otherwise unknown
    if (!(top && editionUnits(m, ed).includes(top))) return null;
  }
  const ref = segs.join(':');
  return { unit, ref: ref !== unit ? ref : null };
}

/* Calendar-keyed works: today's unit ref from the work's own calendar (offline via Intl). */
function todayUnit(m) {
  if (!m.calendar) return null;
  const fmt = new Intl.DateTimeFormat('en-u-ca-' + m.calendar, { month: 'numeric', day: 'numeric', year: 'numeric' });
  const parts = Object.fromEntries(fmt.formatToParts(new Date()).map(p => [p.type, p.value]));
  const key = m.dateKey || '{MM}-{DD}';
  return key.replace('{MM}', String(parts.month).padStart(2, '0')).replace('{DD}', String(parts.day).padStart(2, '0'))
            .replace('{M}', parts.month).replace('{D}', parts.day);
}

/* ---------------- Library panel ---------------- */
function renderLibrary() {
  const body = $('#library-body'); body.innerHTML = '';
  for (const t of S.registry.traditions.filter(t => t.enabled)) {
    const open = S.tradition === t.id;
    const box = el('div', { class: 'tradition' + (open ? ' open' : '') });
    box.append(el('button', { class: 'trad-head', onclick: () => { S.tradition = open ? null : t.id; S.family = ''; renderLibrary(); } }, t.label, el('span', { class: 'muted', text: open ? '−' : '+' })));
    if (open) box.append(renderTraditionBody(t));
    body.append(box);
  }
}
function renderTraditionBody(t) {
  const wrap = el('div', { class: 'trad-body' });
  if (t.families?.length) {
    const sel = el('select', { onchange: e => { S.family = e.target.value; renderLibrary(); if (S.work) renderEditionPicker(); } }, el('option', { value: '', text: 'All families' }));
    for (const f of t.families) sel.append(el('option', { value: f.id, text: f.label, selected: S.family === f.id }));
    wrap.append(el('div', { class: 'family-row' }, 'Family', sel));
  }
  const shelves = [['scripture', 'Scripture'], ['documents', 'Foundational Documents'], ['devotional', 'Devotional & Daily Reading']];
  for (const [key, label] of shelves) {
    const sh = el('div', { class: 'shelf' }, el('h4', { text: label }));
    const ids = t.shelves?.[key] || [];
    if (!ids.length) sh.append(el('div', { class: 'empty', text: 'Nothing on this shelf in this build.' }));
    const items = ids.map(id => ({ id, m: S.manifests.get(id) })).sort((a, b) => familyRank(a.m?.families, S.family) - familyRank(b.m?.families, S.family));
    for (const { id, m } of items) {
      if (!m) { sh.append(el('div', { class: 'empty', text: id + ' (missing manifest)' })); continue; }
      sh.append(el('button', { class: 'work-btn' + (S.work === id ? ' active' : ''), onclick: () => openWork(id, t.id) },
        L(m.title), m.subtitle ? el('span', { class: 'sub', text: L(m.subtitle) }) : null));
    }
    wrap.append(sh);
  }
  return wrap;
}

/* ---------------- Opening works and units ---------------- */
async function openWork(workId, traditionId, opts = {}) {
  const m = await manifest(workId);
  S.work = workId; S.tradition = traditionId || m.tradition; S.docs.clear();
  const sorted = sortedEditions(m);
  let eds = opts.editions?.filter(id => m.editions.some(e => e.id === id));
  if (!eds?.length) {
    const primary = (S.family && sorted.find(e => e.families?.includes(S.family))) || m.editions.find(e => e.id === m.defaultEditions?.[0]) || m.editions[0];
    const second = (m.defaultEditions || []).map(id => m.editions.find(e => e.id === id)).find(e => e && e.id !== primary.id);
    eds = [primary.id, second?.id].filter(Boolean);
  }
  S.editions = eds;
  closePanels(); renderLibrary();
  $('#welcome').hidden = true; $('#work-head').hidden = false; $('#unit-nav').hidden = false;
  $('#work-title').innerHTML = ''; $('#work-title').append(L(m.title), m.subtitle ? el('span', { class: 'sub', text: L(m.subtitle) }) : '');
  $('#btn-today').hidden = !m.calendar;
  renderEditionPicker();
  let unit = opts.unit;
  if (!unit) { const units = editionUnits(m, primaryEdition()); unit = (m.calendar && todayUnit(m)) || units.find(u => unitAvailable(primaryEdition(), u)) || units[0]; }
  await openUnit(unit, opts.ref);
}
const primaryEdition = () => S.manifests.get(S.work).editions.find(e => e.id === S.editions[0]);
const editionObj = id => S.manifests.get(S.work).editions.find(e => e.id === id);

function renderEditionPicker() {
  const m = S.manifests.get(S.work); const box = $('#work-editions'); box.innerHTML = '';
  const sorted = sortedEditions(m);
  const mk = (slot) => {
    const sel = el('select', { onchange: e => { S.editions[slot] = e.target.value || undefined; S.editions = S.editions.filter(Boolean); if (!S.editions.length) S.editions = [m.editions[0].id]; openUnit(S.unit); } });
    if (slot === 1) sel.append(el('option', { value: '', text: '— compare with —', selected: !S.editions[1] }));
    const langs = new Map();
    for (const e of sorted) { const k = e.lang || 'und'; if (!langs.has(k)) langs.set(k, []); langs.get(k).push(e); }
    const langName = k => { try { return new Intl.DisplayNames(['en'], { type: 'language' }).of(k) || k; } catch { return k; } };
    const keys = [...langs.keys()].sort((a, b) => (a === 'en' ? -1 : b === 'en' ? 1 : langName(a).localeCompare(langName(b))));
    for (const k of keys) {
      const parent = langs.size > 1 ? el('optgroup', { label: langName(k) }) : sel;
      for (const e of langs.get(k)) parent.append(el('option', { value: e.id, text: L(e.label), selected: S.editions[slot] === e.id }));
      if (parent !== sel) sel.append(parent);
    }
    return sel;
  };
  box.append(mk(0));
  if (m.editions.length > 1) box.append(mk(1));
}

async function openUnit(unit, ref) {
  const m = S.manifests.get(S.work); S.unit = unit;
  $('#toc').hidden = true;
  const eds = S.editions.map(editionObj);
  const docs = await Promise.all(eds.map(async e => {
    if (!unitAvailable(e, unit) || !editionUnits(m, e).includes(unit)) return null;
    try { return await Lib.load(unitPath(S.work, e.id, unit)); } catch { return null; }
  }));
  renderCrumb(m); renderReader(m, eds, docs); updateNav(m);
  const hash = `#${S.work}/${S.editions.join('+')}/${unit}` + (ref ? '/' + ref : '');
  S.lastHash = hash; history.replaceState(null, '', hash); localStorage.setItem('reader:last', hash);
  window.scrollTo({ top: 0 });
  if (ref) { const cell = document.querySelector(`.row[data-ref="${CSS.escape(ref)}"]`); if (cell) { cell.scrollIntoView({ block: 'center' }); cell.querySelectorAll('.cell').forEach(c => c.classList.add('highlight')); } }
}
function renderCrumb(m) {
  $('#crumb-tradition').textContent = traditionOf(S.tradition)?.label || '';
  $('#crumb-work').textContent = L(m.title);
  $('#crumb-unit').textContent = unitLabel(m, S.unit);
  $('#btn-toc').textContent = unitLabel(m, S.unit);
}
function renderReader(m, eds, docs) {
  const r = $('#reader'); r.innerHTML = '';
  if (m.notes) r.append(el('div', { class: 'work-note', text: L(m.notes) }));
  const cols = eds.length;
  const heads = el('div', { class: 'col-heads', style: `grid-template-columns: repeat(${cols}, 1fr)` });
  eds.forEach(e => heads.append(el('div', { dir: e.direction || 'ltr', text: L(e.label) + (e.role === 'original' ? ' · original' : '') })));
  if (cols > 1) r.append(heads);
  // merged reference order: primary's order, then refs only in other editions inserted after their predecessor
  const order = docs[0] ? docs[0].passages.map(p => p.ref) : [];
  for (let i = 1; i < docs.length; i++) {
    if (!docs[i]) continue;
    let prev = null;
    for (const p of docs[i].passages) {
      if (!order.includes(p.ref)) { const at = prev ? order.indexOf(prev) + 1 : order.length; order.splice(at, 0, p.ref); }
      prev = p.ref;
    }
  }
  if (!order.length) { r.append(el('p', { class: 'muted', text: 'This section is not available in the selected edition' + (cols > 1 ? 's.' : '.') })); return; }
  if (cols > 1 && docs.some(d => !d)) {
    const notice = el('div', { class: 'row notice', style: `grid-template-columns: repeat(${cols}, 1fr)` });
    eds.forEach((e, i) => notice.append(el('div', { class: docs[i] ? 'cell' : 'cell missing', text: docs[i] ? '' : `${unitLabel(m, S.unit)} is not part of this edition.` })));
    r.append(notice);
  }
  const maps = docs.map(d => d ? new Map(d.passages.map(p => [p.ref, p])) : null);
  const vn = ref => ref.split(':').pop();
  for (const ref of order) {
    const row = el('div', { class: 'row' + (cols === 1 ? ' single' : ''), 'data-ref': ref, style: `grid-template-columns: repeat(${cols}, 1fr)` });
    eds.forEach((e, i) => {
      const p = maps[i]?.get(ref);
      if (!p) { row.append(el('div', { class: 'cell missing' + (docs[i] ? '' : ' blank'), 'data-label': L(e.label), text: docs[i] ? 'Not in this edition' : '' })); return; }
      const cell = el('div', { class: 'cell', dir: e.direction || 'ltr', 'data-script': e.script || 'Latn', 'data-label': L(e.label), title: cite(m, ref) });
      if (p.heading) cell.append(el('span', { class: 'heading', text: p.heading }));
      cell.append(el('span', { class: 'vn', text: vn(ref) }));
      const t = el('span'); t.innerHTML = renderMarkup(p.text); cell.append(t);
      if (p.notes?.length) {
        const fn = el('ol', { class: 'fn' });
        p.notes.forEach((n, k) => fn.append(el('li', { text: n.text })));
        cell.append(el('sup', { class: 'fn-mark', text: `[${p.notes.length === 1 ? '†' : p.notes.length + ' notes'}]`, title: p.notes.map(n => n.text).join('\n') }), fn);
      }
      row.append(cell);
    });
    r.append(row);
  }
}

/* ---------------- Table of contents ---------------- */
function toggleToc() {
  const box = $('#toc'); if (!box.hidden) { box.hidden = true; return; }
  const m = S.manifests.get(S.work), ed = primaryEdition(); box.innerHTML = ''; box.hidden = false;
  if (isBibleLike(m)) {
    const [curBook] = S.unit.split(':');
    const books = m.canons[ed.canon] || Object.keys(m.books);
    const grid = el('div', { class: 'toc-grid' });
    for (const b of books) grid.append(el('button', { class: b === curBook ? 'active' : '', onclick: () => { showChapters(b); } }, L(m.books[b])));
    box.append(el('h3', { text: `Books — ${L(ed.label)} (${books.length})` }), grid);
    const chBox = el('div'); box.append(chBox);
    const showChapters = (b) => {
      chBox.innerHTML = ''; const g = el('div', { class: 'toc-grid' });
      for (let c = 1; c <= (m.chapters[b] || 1); c++) {
        const u = `${b}:${c}`;
        g.append(el('button', { class: (u === S.unit ? 'active ' : '') + (unitAvailable(ed, u) ? '' : 'unavailable'), onclick: () => openUnit(u) }, String(c)));
      }
      chBox.append(el('h3', { text: `${L(m.books[b])} — chapters` }), g);
    };
    showChapters(curBook);
  } else {
    const list = el('div', { class: 'toc-list' });
    for (const t of m.toc || []) {
      if (t.children) { list.append(el('div', { class: 'toc-group', text: L(t.label) })); for (const c of t.children) list.append(tocBtn(c, ed)); }
      else list.append(tocBtn(t, ed));
    }
    box.append(list);
  }
  function tocBtn(t, ed) {
    const alt = Object.entries(t.label || {}).filter(([k]) => k !== 'en')[0];
    return el('button', { class: (t.ref === S.unit ? 'active' : '') + (unitAvailable(ed, t.ref) ? '' : ' unavailable'), onclick: () => openUnit(t.ref) },
      `${L(t.label)}`, alt ? el('span', { class: 'alt', dir: /^[֐-ࣿ]/.test(alt[1]) ? 'rtl' : 'ltr', text: alt[1] }) : null, t.count ? el('span', { class: 'alt', text: `· ${t.count}` }) : null);
  }
}
function updateNav(m) {
  const ed = primaryEdition(); const units = editionUnits(m, ed).filter(u => unitAvailable(ed, u)); const i = units.indexOf(S.unit);
  $('#float-nav').hidden = false;
  for (const [id, off] of [['#btn-prev', -1], ['#btn-prev-f', -1], ['#btn-next', 1], ['#btn-next-f', 1]]) {
    const b = $(id); const t = units[i + off]; b.disabled = !t; b.title = t ? unitLabel(m, t) : '';
  }
}
function step(delta) {
  const m = S.manifests.get(S.work), ed = primaryEdition();
  const units = editionUnits(m, ed).filter(u => unitAvailable(ed, u));
  const i = units.indexOf(S.unit); const next = units[i + delta];
  if (next) openUnit(next);
}

/* ---------------- Search ---------------- */
const searchCache = new Map();
async function searchIndex(workId, edId) {
  const key = `${workId}/${edId}`;
  if (!searchCache.has(key)) {
    let data = await Lib.load(`search/${workId}/${edId}`).catch(() => null);
    if (!data) {   // no prebuilt index: scan the edition's unit files (all local in bundle/file mode)
      const m = await manifest(workId), ed = m.editions.find(e => e.id === edId);
      const refs = [], text = [];
      const units = editionUnits(m, ed).filter(u => unitAvailable(ed, u));
      for (let i = 0; i < units.length; i += 25) {
        const docs = await Promise.all(units.slice(i, i + 25).map(u => Lib.load(unitPath(workId, edId, u)).catch(() => null)));
        for (const d of docs) if (d) for (const p of d.passages) { refs.push(p.ref); text.push(p.text.replace(/\[\[|\]\]|\*\*|\*|(^|\s)_|_(?=[\s.,;:!?)]|$)/g, '')); }
      }
      data = { refs, text };
    }
    searchCache.set(key, { refs: data.refs, text: data.text, folded: data.text.map(fold) });
  }
  return searchCache.get(key);
}
async function runSearch(q) {
  const out = $('#search-results'), status = $('#search-status'); out.innerHTML = '';
  const words = fold(q).s.split(/\s+/).filter(Boolean);
  if (!words.length) return;
  const scope = $('#search-scope').value;
  const targets = [];
  if (scope === 'work' && S.work) targets.push(...S.editions.map(e => [S.work, e]));
  else if (S.tradition) {
    const t = traditionOf(S.tradition);
    for (const ids of Object.values(t.shelves)) for (const w of ids) {
      const m = S.manifests.get(w); if (!m) continue;
      const eds = w === S.work ? S.editions : [m.defaultEditions?.[0] || m.editions[0].id];
      for (const e of eds) targets.push([w, e]);
    }
  }
  status.textContent = 'Searching…';
  let n = 0; const MAX = 300;
  for (const [w, e] of targets) {
    const idx = await searchIndex(w, e); const m = S.manifests.get(w); const ed = m.editions.find(x => x.id === e);
    for (let i = 0; i < idx.refs.length && n < MAX; i++) {
      const f = idx.folded[i];
      const pos = words.map(wd => f.s.indexOf(wd));
      if (pos.some(p => p < 0)) continue;
      n++;
      const ref = idx.refs[i];
      const li = el('li', { onclick: () => { const unitDepth = m.levels.findIndex(l => l.isUnit) + 1; openWork(w, m.tradition, { editions: w === S.work ? S.editions : [e], unit: ref.split(':').slice(0, unitDepth).join(':'), ref }); } });
      li.append(el('div', { class: 'ref', text: `${cite(m, ref)}${targets.length > 1 ? ' · ' + L(ed.label) : ''}` }));
      if (m.previewPolicy !== 'reference-only') {
        const sn = el('div', { class: 'snippet', dir: ed.direction || 'ltr', 'data-script': ed.script });
        sn.innerHTML = highlight(idx.text[i], f, words);
        li.append(sn);
      }
      out.append(li);
    }
  }
  status.textContent = n ? `${n}${n >= MAX ? '+' : ''} result${n === 1 ? '' : 's'}` : 'No results';
}
function highlight(orig, f, words) {
  const spans = [];
  for (const w of words) { let p = f.s.indexOf(w); while (p >= 0) { spans.push([f.map[p], f.map[p + w.length]]); p = f.s.indexOf(w, p + 1); } }
  spans.sort((a, b) => a[0] - b[0]);
  let html = '', at = 0;
  for (const [a, b] of spans) { if (a < at) continue; html += esc(orig.slice(at, a)) + '<mark>' + esc(orig.slice(a, b)) + '</mark>'; at = b; }
  return html + esc(orig.slice(at));
}
function renderSearchScope() {
  const sel = $('#search-scope'); sel.innerHTML = '';
  if (S.work) sel.append(el('option', { value: 'work', text: 'This work' }));
  if (S.tradition) sel.append(el('option', { value: 'tradition', text: traditionOf(S.tradition).label }));
}

/* ---------------- Panels & settings ---------------- */
function openPanel(id) { closePanels(); $('#' + id).hidden = false; $('#backdrop').hidden = false; if (id === 'search') { renderSearchScope(); $('#search-input').focus(); } }
function closePanels() { for (const p of document.querySelectorAll('.panel')) p.hidden = true; $('#backdrop').hidden = true; }
function applySettings() {
  const s = S.settings; const b = document.body;
  b.dataset.theme = s.theme; b.dataset.font = s.font; b.dataset.layout = s.layout; b.classList.toggle('show-numbers', !!s.numbers); b.classList.toggle('show-footnotes', !!s.footnotes);
  document.documentElement.style.setProperty('--size', s.size + 'px'); document.documentElement.style.setProperty('--leading', s.leading);
  for (const r of document.querySelectorAll('input[type=radio]')) r.checked = s[r.name] === r.value;
  $('#size').value = s.size; $('#size-out').value = s.size + 'px'; $('#leading').value = s.leading; $('#leading-out').value = s.leading; $('#show-numbers').checked = !!s.numbers; $('#show-footnotes').checked = !!s.footnotes;
  localStorage.setItem('reader:settings', JSON.stringify(s));
}

/* ---------------- Boot ---------------- */
async function boot() {
  S.registry = await Lib.load('registry');
  const ids = new Set(); for (const t of S.registry.traditions) if (t.enabled) for (const list of Object.values(t.shelves || {})) list.forEach(id => ids.add(id));
  await Promise.all([...ids].map(id => manifest(id).catch(() => null)));
  applySettings(); renderLibrary();

  $('#btn-library').onclick = $('#btn-welcome-library').onclick = () => openPanel('library');
  $('#btn-search').onclick = () => openPanel('search');
  $('#btn-settings').onclick = () => openPanel('settings');
  $('#backdrop').onclick = closePanels;
  for (const b of document.querySelectorAll('[data-close]')) b.onclick = closePanels;
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closePanels(); if (e.target.tagName === 'INPUT') return; if (e.key === 'ArrowRight' || e.key === 'j') step(1); if (e.key === 'ArrowLeft' || e.key === 'k') step(-1); });
  $('#btn-prev').onclick = $('#btn-prev-f').onclick = () => step(-1);
  $('#btn-next').onclick = $('#btn-next-f').onclick = () => step(1);
  $('#btn-top-f').onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
  $('#btn-toc').onclick = toggleToc;
  $('#btn-today').onclick = () => { const u = todayUnit(S.manifests.get(S.work)); if (u) openUnit(u); };
  $('#ref-form').onsubmit = e => {
    e.preventDefault(); if (!S.work) return;
    const r = parseRef(S.manifests.get(S.work), $('#ref-input').value);
    if (r) { openUnit(r.unit, r.ref); $('#ref-input').value = ''; } else $('#ref-input').select();
  };
  $('#search-form').onsubmit = e => { e.preventDefault(); runSearch($('#search-input').value); };
  for (const r of document.querySelectorAll('input[type=radio]')) r.onchange = () => { S.settings[r.name] = r.value; applySettings(); };
  $('#size').oninput = e => { S.settings.size = +e.target.value; applySettings(); };
  $('#leading').oninput = e => { S.settings.leading = +e.target.value; applySettings(); };
  $('#show-numbers').onchange = e => { S.settings.numbers = e.target.checked; applySettings(); };
  $('#show-footnotes').onchange = e => { S.settings.footnotes = e.target.checked; applySettings(); };

  const openHash = async (hash) => {
    const mt = (hash || '').match(/^#([\w-]+)\/([\w+-]+)\/([^/]+)(?:\/(.+))?$/);
    if (!mt || !ids.has(mt[1])) return false;
    try { await openWork(mt[1], null, { editions: mt[2].split('+'), unit: decodeURIComponent(mt[3]), ref: mt[4] && decodeURIComponent(mt[4]) }); } catch (e) { console.error(e); }
    return true;
  };
  window.addEventListener('hashchange', () => { const h = location.hash; if (h && h !== S.lastHash) openHash(h); });
  await openHash(location.hash) || await openHash(localStorage.getItem('reader:last'));
}
boot().catch(e => { console.error(e); $('#welcome').innerHTML = `<h1>Could not start</h1><p class="muted">${esc(e.message)}</p>`; });
})();
