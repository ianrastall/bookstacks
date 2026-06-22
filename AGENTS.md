# Bookstacks Agent Notes

## Repo Shape

- This is an [Astro](https://astro.build) static site for public domain texts.
- The reading content lives directly in `authors/<author-slug>/<book-slug>/` as
  Markdown. Treat those files as the source of truth.
- A single content collection (`src/content.config.ts`) loads `authors/**/*.md`
  and validates front matter with a Zod schema.
- All site code lives under `src/`. There is no repo-local `books/` source
  library, `migrate_books.py`, `books/catalog.json`, or per-book `nav.json`.
- Raw Project Gutenberg HTML may be dropped in temporarily for import; it is not
  a long-term site asset and should be removed once converted or identified as a
  duplicate.
- Images live under `img/`, usually grouped by author slug.
- Files in `public/` (currently `CNAME`) are copied to the site root verbatim at
  build time.
- `seed_indexes.py` only creates missing author and book index files. It does
  not split books, rewrite chapter content, or update existing index files.

## Source Layout

- `src/content.config.ts` — the `authors` collection: a glob loader over
  `authors/**/*.md` plus the front-matter schema (all fields optional in the
  schema; required in practice per page type).
- `src/pages/index.astro` — home page; lists authors and counts.
- `src/pages/authors/[...slug].astro` — the one dynamic route for every author
  index, book index, and chapter. `getStaticPaths` derives each slug from the
  file id (stripping a trailing `/index`), and the template branches on the
  `layout` value.
- `src/layouts/BaseLayout.astro` — page shell: header, site network, footer,
  Material Icons, and the inline theme-toggle / accent-color scripts (formerly
  `assets/js/theme.js`).
- `src/styles/global.css` — all styling (formerly `assets/css/style.css`).
- `astro.config.mjs` — `site: https://bookstacks.org`, `output: 'static'`,
  `build.format: 'file'` (pages emit as `<name>.html`, not `<name>/index.html`).

## Content Structure

- Author index pages use:

```yaml
---
layout: author_index
title: "Jane Austen"
author_name: "Jane Austen"
---
```

- Book index pages use:

```yaml
---
layout: book_index
title: "Pride and Prejudice"
book_title: "Pride and Prejudice"
author: "Jane Austen"
---
```

- Chapter pages use:

```yaml
---
layout: book
title: "Chapter 1"
chapter_order: 1
book: "Pride and Prejudice"
author: "Jane Austen"
---
```

- Chapter pages may also set `toc_title` to override the link text in the book
  TOC. `toc_section` is in the schema but is not currently consumed by any
  template; treat it as reserved rather than functional.
- Place chapters at `authors/<author-slug>/<book-slug>/chapter-N.md`.
- Use lowercase hyphenated slugs. Existing author slugs generally use
  `surname-given`, for example `austen-jane`.
- Keep `chapter_order` numeric and sequential within a book. The table of
  contents and chapter navigation sort by this value, not by filename order.
- Keep `book` and `author` values consistent across every chapter in the same
  book. `seed_indexes.py` uses the most common chapter values when creating a
  missing book index.
- Use UTF-8 text. Existing content includes typographic punctuation; preserve
  the style already used by the surrounding text.
- Prefer plain Markdown prose. Do not introduce raw HTML in chapter files unless
  the surrounding content requires it.

## Rendering Behavior To Remember

- `layout` is a view selector read by `src/pages/authors/[...slug].astro`, not a
  reference to a layout file. The three values map to the author-index,
  book-index, and chapter views inside that one component.
- The author view lists pages with `layout: book_index` whose id is under the
  current author slug, sorted by `book_title`.
- The book view lists pages with `layout: book` under the current book prefix,
  sorted by `chapter_order`, and renders a **flat** ordered list of chapter
  links (`toc_title` or `title`). There is no section grouping or nested
  body-heading extraction — unlike the old Jekyll TOC, chapter body headings are
  not pulled into the table of contents.
- The chapter view builds breadcrumbs from the slug, renders the chapter title
  as an `<h2 class="navchap">` followed by `<Content />`, and computes
  previous/next links from the sorted chapter list.
- Reading styles are under `.reader-content`; chapter layout and the sticky
  side navigation use `.chapter-container`, `.chapter-layout`,
  `.chapter-sidebar`, `.chapter-navigation`, and `.chapter-nav-button` in
  `global.css`.
- Keep layout changes compatible with the existing dark/light theme variables
  and the accent-color CSS custom properties (`--accent`, `--accent-strong`).

## Legacy Concepts (Do Not Reintroduce)

- Old v0 `books/<author>/<book>/<author-book>.html` source files have no
  equivalent. Each chapter Markdown file is the editable source.
- Old v0 `class="navchap"` splitter headings are replaced by one `chapter-*.md`
  file per rendered chapter. Heading-hierarchy rules are replaced by explicit
  `chapter_order` front matter.
- Old `books/catalog.json` and per-book `nav.json` are replaced by Astro content
  collection queries over front matter.
- The earlier Jekyll layouts (`_layouts/`, `_includes/`) and Liquid templates
  are gone; do not look for them. Their behavior now lives in the `src/` Astro
  components described above.

## Working Rules

- When fixing text, edit the relevant `authors/.../chapter-*.md` file directly
  and keep the YAML front matter intact.
- When adding a new book, add all chapter files plus the book index. Add the
  author index too if it is a new author.
- When importing raw Gutenberg HTML, delete each raw input after it has been
  converted into Markdown or identified as a duplicate.
- When only missing indexes need filling in, run `python seed_indexes.py`. It is
  intentionally conservative: it only writes an index file that does not already
  exist.
- Keep generated/cache output out of commits, especially `dist/` and `.astro/`
  (both are git-ignored).
- Be careful with broad searches in `authors/`; the corpus is large. Prefer
  scoped paths when inspecting or editing a specific author or book.

## Raw Gutenberg Imports

- Always check for duplicates before creating new books: by normalized title
  against existing book slugs, and by normalized title against existing chapter
  titles for the same author.
- If a raw file is a duplicate, remove it and do not create another book
  directory.
- If a raw file is new, convert it into `authors/<author-slug>/<book-slug>/index.md`
  plus chapter Markdown files in the current content model.
- Extract the author and title from the source metadata or visible title block,
  then reuse the existing author slug if that author is already present.
- Strip Project Gutenberg boilerplate, license text, generated contents pages,
  transcriber notes, HTML navigation, and other non-reading scaffolding.
- Preserve the work's reading structure. Many Gutenberg files are single
  stories, but some contain introductory sections, after-story sections,
  roman-numeral parts, verse, or grouped sketches that should become separate
  chapter files when they render as separate reading sections.
- After conversion, verify there are no remaining raw Gutenberg markers and
  delete the handled raw input file.

## Adding Or Converting A Book

1. Choose slugs and create `authors/<author-slug>/<book-slug>/`.
2. Split the source text into one Markdown file per rendered chapter or section.
3. Name files `chapter-1.md`, `chapter-2.md`, and so on unless an existing local
   pattern says otherwise.
4. Add chapter front matter with `layout: book`, `title`, `chapter_order`,
   `book`, and `author`.
5. Put only the chapter body after the front matter. The chapter view already
   renders `title` as the chapter heading.
6. Remove Gutenberg boilerplate, license text, generated contents, navigation
   scaffolding, and trailing ephemera that is not part of the reading text.
7. Preserve the reading text's paragraphing, verse lineation, emphasis, and
   notes as plain Markdown wherever possible.
8. Inline or adapt footnotes only when needed for readability, keeping the
   result in the chapter where the note marker appears.
9. Add `index.md` files for the author and book, or run `python seed_indexes.py`
   after the chapters are in place.

## Text Editing Guidance

- Preserve public domain reading text unless the task is explicitly to correct
  it.
- Preserve paragraph boundaries, blank lines, and emphasis markers already
  present in the source.
- Do not normalize curly quotes, dashes, accents, or spelling unless the user
  asks for that specific cleanup.
- Do not remove apparent archaic spelling or punctuation just because it looks
  unusual.
- If adding images to chapter content, keep paths root-relative and verify they
  resolve under the chapter's URL.

## Verification

- For template or layout changes, run a type check and build:

```powershell
npm run build
```

  This runs `astro check` (TypeScript / content-schema validation) and then
  `astro build`. Full builds can take several minutes because the library
  contains thousands of chapters; allow a long timeout.

- For a quick visual check, use the dev server instead of a full build:

```powershell
npm run dev
```

- For content-only changes, verifying front matter and paths is usually enough.
- After adding or moving chapters, verify:
  - the author index exists at `authors/<author-slug>/index.md`;
  - the book index exists at `authors/<author-slug>/<book-slug>/index.md`;
  - every chapter has `layout: book`;
  - every chapter has a numeric `chapter_order`;
  - chapter orders are unique within the book;
  - every chapter has the intended `book` and `author` front matter;
  - the table of contents and previous/next navigation render in the expected
    order.

## Useful Commands

```powershell
python seed_indexes.py
```

```powershell
npm run build
```

```powershell
rg -n "layout: book|chapter_order:" authors\<author-slug>\<book-slug>
```
