# Bookstacks Agent Notes

## Repo Shape

- An [Astro](https://astro.build) static site for public domain texts at
  bookstacks.org.
- **One TEI XML file per book** lives in `tei-source/`, named
  `<gutenberg-id>-full.xml`. These files are the source of truth for the entire
  library. Do not split a book into many files — one book is one file.
- A single content collection (`src/content.config.ts`) parses every
  `tei-source/*.xml` with a custom loader and emits the author / book / chapter
  entries the pages consume. There is no Markdown content tree and no per-book
  index files.
- All site code lives under `src/`.
- Files in `public/` are copied to the site root verbatim at build time
  (`CNAME`, `img/authors/<slug>.png` portraits).

## Source Layout

- `tei-source/<id>-full.xml` — the TEI book files.
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
2. Create `tei-source/<gutenberg-id>-full.xml`.
3. Write the `teiHeader` with the registries, then the `text/body` chapter divs
   using the conventions above.
4. Strip Project Gutenberg boilerplate, license text, generated contents, and
   transcriber notes. Keep the work's own reading structure.
5. Optionally add a duotone portrait at `public/img/authors/<slug>.png` (see README).
6. Build to verify (below).

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
