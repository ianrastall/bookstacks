# Bookstacks

Bookstacks is an [Astro](https://astro.build) static site for reading public
domain literature at <https://bookstacks.org>.

The library is built from **one TEI XML file per book**. A custom content-collection
loader parses every file in `tei-source/` at build time and generates the author
pages, book tables of contents (with character and place registries), and
individual chapter reading pages.

## Project Structure

- `tei-source/<gutenberg-id>-full.xml` (or `-*.xml`): the TEI source for a book. While most books are a single `-full.xml` file, parallel-text books can be split by language (e.g., `2600-ru.xml`, `2600-en.xml`); the parser will auto-discover and merge them at build time.
- `src/utils/teiParser.ts`: parses a TEI file into `{ title, author, persons,
  places, chapters }` and converts each chapter's TEI body to reading HTML.
- `src/content.config.ts`: defines the `authors` content collection. A custom
  loader reads every `tei-source/*.xml` and emits synthetic entries — one
  `author_index`, one `book_index` (carrying the person/place registries), and
  one `book` (chapter) entry per chapter.
- `src/pages/index.astro`: the home page. Lists every author as a card and reports
  author / book / chapter counts.
- `src/pages/authors/[...slug].astro`: one dynamic route that renders every author
  index, book index (table of contents + registries), and chapter reading page. It
  branches on the `layout` value of the entry.
- `src/layouts/BaseLayout.astro`: the shared page shell — header, site network,
  footer, Material Icons, and the inline theme / accent-color scripts.
- `src/styles/global.css`: all theme, index, table-of-contents, registry, and
  reader styles.
- `public/`: files copied verbatim to the site root at build time, including
  `CNAME` (custom domain) and `img/authors/<slug>.png` portraits.
- `.github/workflows/deploy.yml`: builds the site and deploys it to GitHub Pages
  on every push to `main`.

## Content Model

Most books are a single TEI document under `tei-source/`, named by their Project
Gutenberg ebook id (e.g. `1342-full.xml` for *Pride and Prejudice*). Books with
multiple parallel translations can be split into language-specific files (e.g.
`2600-ru.xml`, `2600-en.xml`, `2600-es.xml` for *War and Peace*). A document has:

- A `teiHeader` with the `title`, `author` (`<persName>`), source credit
  (`<sourceDesc>`), and the registries: `<particDesc><listPerson>` for characters
  and `<settingDesc><listPlace>` for places. Each `<person>` / `<place>` has an
  `xml:id`, a name, and a short `<note>`.
- A `<text><body>` containing one `<div type="chapter" n="N">` per chapter, each
  with a `<head>` (the chapter title) followed by the chapter content.

Slugs are derived automatically: the author slug is `surname-given`
(`austen-jane`, `tolstoy-leo`); the book slug is the slugified title
(`pride-and-prejudice`, `war-and-peace`). The chapter `n` attribute becomes the
chapter order and **must be unique within a book**.

### Reading markup

The chapter body is semantically encoded, not a transliteration of any edition's
presentational markup. The parser understands:

- `<p>` paragraphs, `<emph>` emphasis, `<title>` work titles (rendered as `<cite>`),
  `<foreign xml:lang="…">` foreign phrases.
- `<said who="#id" direct="true">` direct speech, attributed to a person in the
  registry.
- `<persName ref="#id">`, `<placeName ref="#id">`, and `<rs ref="#id">` references,
  which resolve to registry entries and render as hover-tooltips in the reader.
- `<pb n="…"/>` page-break milestones; verse via `<lg>` / `<l>`; correspondence via
  `<floatingText>`, `<opener>`, `<closer>`, `<salute>`, `<signed>`, `<dateline>`.

## Adding A Book

1. Create `tei-source/<gutenberg-id>-full.xml` (or split by language for parallel texts).
2. Write the `teiHeader` (title, author, source credit, and the person/place
   registries).
3. Add `<div type="chapter" n="N">` blocks under `<text><body>`, each with a
   `<head>` and the chapter content, using the reading markup above.
4. Optionally add a portrait at `public/img/authors/<author-slug>.png` (see below).

That's it — the loader and the dynamic route pick the book up automatically. There
are no per-book index files to maintain.

## Author Portraits

Portraits are optional. If `public/img/authors/<author-slug>.png` exists, the home
page and author page show it; otherwise a fallback icon is used.

Portraits are **duotone tiles** (a colored ground plus dark ink) so they render
correctly in both light and dark themes without inversion, and so each author can
have a distinct color. To make one from a grayscale engraving:

```bash
magick <engraving>.png -resize 500x500 -colorspace Gray \
  +level-colors "#333333","<author-color>" \
  public/img/authors/<author-slug>.png
```

`#333333` is the ink; the second color is that author's ground (e.g. coral for
Austen).

## Local Development

Requires Node.js (18.20.8+, 20.3+, or 22+).

```bash
npm install      # install dependencies
npm run dev      # start the dev server
npm run build    # type-check (astro check) then build into dist/
npm run preview  # preview the built output
```

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the site
and publishes `dist/` to GitHub Pages. The repository's Pages source must be set to
**GitHub Actions**. The custom domain is preserved by `public/CNAME`.

## Public Domain Notice

Works hosted here are intended to be public domain in the United States. Users
outside the United States should verify the copyright status in their own
jurisdiction.
