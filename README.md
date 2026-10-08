# ARC — Agency Religious Codex

ARC is a multi-tradition scripture reader that runs offline. The reader is generic: it knows nothing about any
particular text and is driven entirely by `registry.json` and the per-work `manifest.json` files.
See the spec document ("Multi-Faith Reader — Data Model Spec") for the schema.

## Layout

```
registry.json                 which traditions, families and shelves are enabled
works/<workId>/manifest.json  one work: levels, citation format, toc/canons, editions
works/<workId>/<editionId>/<unit>.json   the text, one file per chapter-sized unit
src/index.html, app.css, app.js          the reader
build.js                      validates, builds search indexes, emits dist/
```

Unit file names are the unit ref with `:` replaced by `-` (`gen:1` → `gen-1.json`; Qur'an surah 2 → `2.json`).

## Build

```
node build.js                       # dist/reader.html (single file) + dist/site/ (split folder)
node build.js --compress            # same, with each inline block deflated (~4:1 on scripture text)
node build.js --only=bundle         # single file only
```

No dependencies: Node 18+ is all that is required.

- `dist/reader.html` is the USB / kiosk deliverable. One file, double-click to open, no server.
  Data is embedded as inert `<script type="text/plain">` blocks, so the browser does not parse the
  library at load; a unit is parsed only when opened. With `--compress`, blocks are inflated on demand
  with the browser's built-in `DecompressionStream`.
- `dist/site/` is for a static web server or an intranet share. Each data file is emitted as `.json`
  (used when served over http) and `.js` (used when `index.html` is opened from disk, where browsers
  block `fetch` of local files). The reader picks the source automatically.

The build fails on structural problems (a shelf naming a work with no manifest, a passage outside its
unit, a file name that does not match its unit) and prints warnings for the rest.

## Reader features

- Library panel: traditions (alphabetical, equal weight) → three shelves → works. Family filter re-sorts
  works and editions; nothing is hidden.
- Two-column comparison of any two editions of a work, rows aligned by reference ID. A passage or unit
  missing from one edition is greyed, never implied. Mixed-direction (RTL beside LTR) works per column.
- "Verse by verse" layout stacks editions under each reference instead of side by side.
- Reference input accepts the tradition's own conventions and aliases (`John 3:16`, `jn 3`, `2:255`,
  `Baqarah 255`, `Nicene 3.2`, `Tobit 1`).
- Search over a pre-built per-edition index, diacritic-insensitive (Arabic tashkeel, Hebrew points, Latin
  accents) with alef and Hebrew final-form folding. Scope: this work or the whole tradition. Never across
  traditions. A work may set `previewPolicy: "reference-only"` to show references without snippets.
- Calendar-keyed works (`"calendar": "gregory" | "hebrew" | "islamic-umalqura"`) open on today's date in
  that calendar, computed offline.
- Display settings (theme, font, size, spacing, layout, verse numbers) and last position persist in the
  browser.
- Keyboard: ← → (or k / j) for previous / next unit; Esc closes panels.

## Adding a work

1. Create `works/<workId>/manifest.json` (copy the nearest existing one: `bible` for book/chapter/verse
   works with a canon list, `quran` for toc-driven works, `nicene-creed` for documents, `spurgeon-me` for
   calendar-keyed devotionals).
2. Add one folder per edition with the unit files.
3. Put the work ID on the right shelf of the right tradition in `registry.json`.
4. `node build.js`.

## Library contents

113 works, 340 MB of text, converted from the sources listed in the spec's "Content sources" tab
(`convert/<tradition>/` holds every converter; each work's manifest records license and source per edition).

- **Baha'i Faith** (8 works) — Scripture: kitab-i-aqdas, kitab-i-iqan, hidden-words, gleanings, prayers-and-meditations; Documents: some-answered-questions, will-and-testament; Devotional: bahai-prayers
- **Buddhism** (14 works) — Scripture: dhammapada, dhammacakkappavattana, satipatthana, anapanasati, metta-sutta, mangala-sutta, kalama-sutta, sigalovada, mahaparinibbana, heart-sutra, diamond-sutra, lotus-sutra, sukhavativyuha; Documents: visuddhimagga
- **Christianity** (46 works) — Scripture: bible, enoch, jubilees; Documents: apostles-creed, nicene-creed, nicene-creed-325, athanasian-creed, chalcedon, council-of-orange, gregory-declaration, ignatius-creed, irenaeus-rule, tertullian-rule, waldensian-confession, thirty-nine-articles, luther-small-catechism, baltimore-catechism, schleitheim, heidelberg, belgic, dort, westminster-confession, westminster-larger, westminster-shorter, scots-confession, second-helvetic, french-confession, tetrapolitan, zwingli-fidei-ratio, first-helvetic, first-basel, consensus-tigurinus, ten-theses-berne, zwingli-67-articles, catechism-young-children, flavel-exposition, henry-scripture-catechism, fisher-catechism-explained, london-1689, keach, baptist-catechism-1695, puritan-catechism, abstract-of-principles; Devotional: spurgeon-me, daily-light, bcp-collects
- **Hinduism** (14 works) — Scripture: bhagavad-gita, isha, kena, katha, prashna, mundaka, mandukya, aitareya, rig-veda, ramayana, ramcharitmanas; Documents: yoga-sutras; Devotional: hanuman-chalisa, vishnu-sahasranama
- **Islam** (14 works) — Scripture: quran; Documents: bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah, malik, nawawi40, tahawiyyah, al-kafi, nahj-al-balagha; Devotional: juz-of-the-day, asma-ul-husna
- **Judaism** (10 works) — Scripture: tanakh; Documents: mishnah, pirkei-avot, talmud-bavli, rambam-13-principles, parashah; Devotional: siddur-edot-hamizrach, siddur-ashkenaz, tehillim-daily, tehillim-weekly
- **Latter-day Saints** (6 works) — Scripture: book-of-mormon, doctrine-and-covenants, pearl-of-great-price, bible; Documents: articles-of-faith, jst-appendix
- **Sikhism** (2 works) — Scripture: guru-granth-sahib; Devotional: nitnem

Known gaps (no open source exists): Augsburg Confession, Catechism of Trent, Wesley's 25 Articles, English
Tahawiyyah, Hisn al-Muslim, English Visuddhimagga, complete Bodhicaryavatara, Chandogya/Brihadaranyaka/Taittiriya
Sanskrit, English Ramcharitmanas, Meqabyan, UHJ Constitution, Come Follow Me schedule.

## Build profiles and sizes

`profiles/<name>.json` restricts a build without touching the data (`--profile=profiles/standard.json`): which
traditions are on, which works are excluded, and for any work which editions are included.

| Build | Command | Size | Opens in | Contents |
| --- | --- | --- | --- | --- |
| standard | `node build.js --compress --only=bundle --profile=profiles/standard.json` | ≈ 296 MB | ≈ 7 s | all traditions; 65 Bibles in 36 languages |
| full | `node build.js --compress --only=bundle` | ≈ 558 MB | ≈ 20 s | everything: 175 Bibles in 59 languages |

Once open, any book opens in well under a second in either build. Use `--max-old-space-size=6000` on `node` for the
full build. Without `--compress` files are ≈ 2.4× larger. `--index` adds prebuilt search indexes (doubles data);
without them the reader scans an edition's units on first search (whole KJV ≈ 5 s), which is fine offline. The
largest works are bible (933 MB raw across 175 editions), talmud-bavli (81 MB), al-kafi (51 MB), guru-granth-sahib (32 MB).

Bible editions marked "© … included under the project's cleared-permission assumption" in their manifest `license`
(ESV, NABRE, NIV, NASB, NKJV, NLT, CSB, AMP, RVR 1960, Schlachter 1951, NVI, and others) are not public domain; drop
them from the profile for any deployment where that permission is not in place.
