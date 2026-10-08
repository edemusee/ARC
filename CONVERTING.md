# Converting texts into the library format

Every converter writes into `works/<workId>/`. It never edits `registry.json` (the integrator does that) and
never edits another work's folder. Run `node build.js --validate-work=<workId>` before reporting done; it
must print the counts with no "Validation:" errors.

## Files

```
works/<workId>/manifest.json
works/<workId>/<editionId>/<unitFile>.json     one per unit; unitFile = unit ref with ':' → '-'
```

## Identifiers

- `workId`, `editionId`, level ids, book codes, toc refs: lowercase ASCII `[a-z0-9-]`, no spaces. Book codes
  for Bibles use the OSIS/Paratext 3-letter set (`gen exo … rev`, deuterocanon `tob jdt wis sir bar 1ma 2ma
  1es 2es 3ma 4ma man ps151 sus bel pra lje`). Enoch `eno`, Jubilees `jub`.
- Reference ID = segments in level order joined by `:` with no work prefix inside files: `gen:1:1`, `2:255`,
  `berakhot:2:a:3`, `1:3` (Ang 1 line 3), `01-01:am`. Segment values are ASCII (`a`/`b` for Talmud sides).
- Unit = the segments up to the level that has `isUnit: true`. Every passage in a unit file has `ref` starting
  with `<unit>:`.

## manifest.json

```json
{
  "schemaVersion": 1,
  "workId": "quran", "tradition": "islam", "shelf": "scripture",
  "families": [],                       // family ids this work belongs to; [] = all
  "title": { "en": "The Qur'an", "ar": "القرآن الكريم" },
  "subtitle": { "en": "…" },            // optional
  "levels": [ { "id": "surah", "label": { "en": "Surah" }, "isUnit": true }, { "id": "ayah", "label": { "en": "Ayah" } } ],
  "citation": { "format": "{work} {surah}:{ayah}", "rangeFormat": "{work} {surah}:{ayah}–{ayah2}", "workAbbrev": { "en": "Qur'an" } },
  "toc": [ { "ref": "1", "label": { "en": "Al-Fatihah", "ar": "الفاتحة" }, "count": 7 } ],   // see below
  "editions": [ {
      "id": "ar-uthmani", "lang": "ar", "script": "Arab", "direction": "rtl",
      "label": { "en": "Arabic (Uthmani)" }, "role": "original",          // original | translation | transliteration | gloss
      "font": "arabic",                                                   // optional: arabic | hebrew | gurmukhi | devanagari
      "families": [],                                                     // optional
      "license": "Public domain", "source": "https://github.com/…",      // REQUIRED: what the repo states
      "canon": "catholic-73"                                              // Bible-like works only
  } ],
  "defaultEditions": ["ar-uthmani", "en-pickthall"],   // max 2; original first where the tradition expects it
  "aliases": { "1": ["fatihah", "al-fatihah"], "jhn": ["john", "jn"] },   // typed-reference names → ref/code
  "notes": { "en": "One sentence shown above the text." },               // optional
  "previewPolicy": "reference-only",                                    // optional (Guru Granth Sahib)
  "calendar": "gregory", "dateKey": "{MM}-{DD}"                           // devotionals only: gregory | hebrew | islamic-umalqura
}
```

Navigation is described one of two ways:

1. **Bible-like** (`book → chapter → verse`, editions differ in which books they contain): instead of `toc`,
   give `books` (`{ "gen": { "en": "Genesis" } }`), `chapters` (`{ "gen": 50 }`), and `canons`
   (`{ "protestant-66": ["gen", …], "catholic-73": [...] }`); each edition names its `canon`. Copy
   `works/bible/manifest.json`.
2. **toc**: ordered entries `{ "ref", "label", "count" }` for the unit level. Two-level navigation
   (tractate → daf; kanda → sarga; book → chapter in hadith) uses `{ "ref": "berakhot", "label": {…},
   "children": [ { "ref": "berakhot:2:a", "label": { "en": "2a" } }, … ] }` where children are the units.

Choose the unit so a unit file is roughly a chapter: a surah, a Bible chapter, a Talmud daf side, a hadith
"book", one day of a devotional, one Ang, one sutta (or one vagga of the Dhammapada), one section of a
confession, one Baha'i work section of up to ~40 paragraphs.

## Unit file

```json
{ "workId": "quran", "editionId": "en-pickthall", "unit": "2",
  "passages": [
    { "ref": "2:1", "text": "Alif. Lam. Mim.", "heading": "In the name of Allah, the Beneficent, the Merciful." },
    { "ref": "2:2", "text": "This is the Scripture whereof there is no doubt, …",
      "notes": [ { "at": 0, "text": "Footnote text." } ] }
  ] }
```

- `text`: plain text, NFC-normalized, single spaces, no leading/trailing whitespace, **no HTML**. Allowed
  inline markup only: `[[word]]` translator-supplied words (KJV italics), `*emphasis*`, `**bold**` (Talmud
  source-text vs. elucidation), `_smallcaps_` (LORD). Line breaks inside a passage (poetry) as `\n`.
- `heading`: optional, text that precedes the passage (pericope title, psalm superscription, bismillah,
  chapter title in a creed, Spurgeon's verse reference). Headings are per edition.
- `notes`: optional footnotes anchored at character offset `at`.
- Passages present in one edition and absent in another are simply absent. Never emit empty-text passages;
  if a source has a numbering hole, skip the ref.
- Keep original verse/paragraph numbering of the tradition. If an edition's numbering differs from the work's
  canonical IDs (Septuagint psalms, English vs Hebrew psalm verses), remap to the canonical ID and say so in the
  edition's `notes`.

## Report back

When done: workId(s), shelf, editions with license, unit/passage counts from the validator, any gaps
(sections skipped, texts not converted, cleanup not done), and where the converter script lives
(`convert/<tradition>/…`). Keep source clones where they are; do not copy raw sources into `works/`.
