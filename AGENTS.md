# Bookstacks Agent Notes

## Repo Shape

- An [Astro](https://astro.build) static site for public domain texts at
  bookstacks.org.
- **TEI XML files** live in `tei-source/`, named `<author-slug>_<title-slug>_<lang>.xml`
  (e.g., `austen-jane_pride-and-prejudice_en.xml`, `tolstoy-leo_war-and-peace_ru.xml`,
  `tolstoy-leo_war-and-peace_en.xml`). Each book uses one XML file per language; the
  parser auto-discovers and merges files sharing the same `<author-slug>_<title-slug>`
  prefix dynamically.
- A single content collection (`src/content.config.ts`) parses every
  `tei-source/*.xml` with a custom loader and emits the author / book / chapter
  entries the pages consume. There is no Markdown content tree and no per-book
  index files.
- All site code lives under `src/`.
- Files in `public/` are copied to the site root verbatim at build time
  (`CNAME`, `img/authors/<slug>.png` portraits).

## Source Layout

- `tei-source/<author-slug>_<title-slug>_<lang>.xml` — the TEI book files.
- `src/utils/teiParser.ts` — `parseTeiBook(file)` returns
  `{ title, author, persons, places, chapters }`. `chapters` is built from
  `<div type="chapter">` elements; `convertNodeToHtml` maps the TEI body to
  reading HTML. `slugify` / `slugifyAuthor` derive the URL slugs.
- `src/content.config.ts` — the `authors` collection. The loader iterates the TEI
  files and `store.set`s one `author_index` per author, one `book_index` per book
  (carrying `persons` and `places`), and one `book` entry per chapter (carrying the
  rendered `html`).
- `src/pages/index.astro` — home page; author cards + counts. An author shows a
  portrait when `public/img/authors/<slug>.png` exists.
- `src/pages/authors/[...slug].astro` — the one dynamic route for every author
  index, book index, and chapter. `getStaticPaths` derives each slug from the entry
  id (stripping a trailing `/index`); the template branches on the `layout` value.
- `src/layouts/BaseLayout.astro` — page shell: header, site network, footer,
  Material Icons, theme-toggle and accent-color scripts.
- `src/styles/global.css` — all styling, including `.tei-registry` (book-index
  registries), `.tei-rs` / `.tei-foreign` (inline reader markup), and the TEI
  correspondence styles.
- `astro.config.mjs` — `site: https://bookstacks.org`, `output: 'static'`,
  `build.format: 'file'` (pages emit as `<name>.html`).

## TEI Encoding Conventions

- Semantic encoding only; do not preserve an edition's presentational markup.
- `teiHeader`: `title`, `author/persName`, a `sourceDesc` crediting the Project
  Gutenberg source, and the registries `particDesc/listPerson` and
  `settingDesc/listPlace`. Each `person` / `place` gets an `xml:id`, a name, and a
  short `note`.
- `text/body` holds `<div type="chapter" n="N">`, each with a `<head>` then content.
  `n` becomes the chapter order and must be unique within the book (number chapters
  globally for multi-book works rather than restarting per book/part).
- Inline markup the parser understands: `p`, `emph`, `title` (→ `<cite>`),
  `foreign[@xml:lang]`, `said[@who][@direct]`, `persName`/`placeName`/`rs` with
  `@ref="#id"` resolving to a registry entry, `pb[@n]`, `lg`/`l` (verse), and the
  correspondence elements (`floatingText`, `opener`, `closer`, `salute`, `signed`,
  `dateline`). Unknown elements fall through to their inner content.
- Inline a translator footnote only as a brief parenthetical gloss where it aids
  reading; otherwise preserve the reading text as-is. Do not normalize curly quotes,
  dashes, or spelling unless explicitly asked.

## Adding Or Converting A Book

1. Identify the author and title; reuse the existing author slug if present.
2. Create `tei-source/<author-slug>_<title-slug>_<lang>.xml` (one per language; all
   language files for a book share the same `<author-slug>_<title-slug>` prefix).
3. Write the `teiHeader` with the registries, then the `text/body` chapter divs
   using the conventions above.
4. Strip Project Gutenberg boilerplate, license text, generated contents, and
   transcriber notes. Keep the work's own reading structure.
5. Optionally add a duotone portrait at `public/img/authors/<slug>.png` (see README).
6. Build to verify (below).

## Parallel-text translations (two-version chapters)

Some books carry an original-language text facing one or more translations, shown
as a **toggle** in the reader. The full conventions live in
[`tei-source/TRANSLATION-STYLE.md`](tei-source/TRANSLATION-STYLE.md) — read it
before translating or encoding such a chapter.

In short: each chapter holds `<div type="version" xml:lang="…" subtype="…">`
blocks (`subtype="original"` / `"translation"`); the reader defaults to the
English/translation version and loops a tab over every version. The parser also
handles `<note>` (inline `[bracket]` gloss), `<seg type="origfr">` (flag for
text that was French in the original), and `<foreign xml:lang>` (dotted-underline
+ language tooltip). **Chapter I of the `tolstoy-leo_war-and-peace_*.xml` files is the
reference chapter.**

### Translation pipeline (War and Peace)

The Russian source comes from Lib.ru (az.lib.ru) HTML, one file per volume,
staged as `*-rus.html` (git-ignored). Convert it with:

```bash
python tools/tei_from_libru.py --in tolstoy-wp-rus.html \
  --volume I --skip 1 --start 2 >> /tmp/chapters.xml
```

The converter emits `<div type="chapter">` blocks (Russian-original version only,
with Tolstoy's footnotes inlined as `<note>` brackets), numbered globally from
`--start`; `--skip` omits already-hand-crafted leading chapters. Splice the
output into `tolstoy-leo_war-and-peace_ru.xml` before `</body>`, then create the English
versions in `tolstoy-leo_war-and-peace_en.xml` per the style guide. The bulk pass does
**not** wrap French in
`<foreign>`; add that (and the `<seg type="origfr">` flags in English) per chapter
during translation.

Phasing: (1) Russian original for the whole novel — Volume I is in; Volumes II–IV
+ epilogues need their source HTML run through the same converter. (2) English
translations, chapter by chapter. (3) optionally a second translation.

Note: the TEI loader calls `store.clear()` each build, so content removed from a
source file is dropped (no stale entries lingering in `.astro`).

## Verification

```bash
npm run build   # astro check (types + content schema) then astro build
```

For a quick visual check use `npm run dev`. After adding a book, confirm:

- the author and book appear on the home page and author page;
- the book index lists the chapters in order and shows the character/place
  registries;
- chapter `n` values are unique within the book;
- previous/next navigation renders in the expected order;
- person/place references resolve (tooltips appear in the reader).

## Working Rules

- Edit the relevant `tei-source/*.xml` file directly; everything else is generated.
- Keep generated/cache output out of commits (`dist/`, `.astro/` — both ignored).
- Do not reintroduce the retired Markdown `authors/**` content model, per-book
  index files, or `seed_indexes.py`; the TEI loader replaces all of them.
