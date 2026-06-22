# Bookstacks

Bookstacks is an [Astro](https://astro.build) static site for reading public
domain literature at <https://bookstacks.org>.

The library is organized directly as Markdown source under `authors/`. A single
Astro content collection loads those files, and the page templates build the
author pages, book tables of contents, and individual chapter reading pages from
their front matter.

## Project Structure

- `src/content.config.ts`: defines the `authors` content collection. It globs
  `authors/**/*.md` and validates front matter with a Zod schema.
- `src/pages/index.astro`: the home page. Lists every author and reports the
  author/book/chapter counts.
- `src/pages/authors/[...slug].astro`: one dynamic route that renders every
  author index, book index (table of contents), and chapter page. It branches on
  the `layout` front matter value to decide which view to render.
- `src/layouts/BaseLayout.astro`: the shared page shell — header, site network,
  footer, Material Icons, and the inline theme / accent-color scripts.
- `src/styles/global.css`: theme, index, table of contents, and reader styles.
- `authors/<author-slug>/index.md`: author landing pages.
- `authors/<author-slug>/<book-slug>/index.md`: book table of contents pages.
- `authors/<author-slug>/<book-slug>/chapter-N.md`: chapter source files.
- `img/`: image assets, generally grouped by author slug.
- `public/`: files copied verbatim to the site root at build time (currently
  `CNAME` for the custom domain).
- `seed_indexes.py`: utility script for creating missing author and book index
  files from existing chapter front matter.
- `.github/workflows/deploy.yml`: builds the site and deploys it to GitHub Pages
  on every push to `main`.

## Content Model

The Markdown front matter is the same model the site has always used; the
`layout` value is now a view selector read by `src/pages/authors/[...slug].astro`
rather than a Jekyll layout file.

Author index pages use:

```yaml
---
layout: author_index
title: "Jane Austen"
author_name: "Jane Austen"
---
```

Book index pages use:

```yaml
---
layout: book_index
title: "Pride and Prejudice"
book_title: "Pride and Prejudice"
author: "Jane Austen"
---
```

Chapter pages use:

```yaml
---
layout: book
title: "Chapter 1"
chapter_order: 1
book: "Pride and Prejudice"
author: "Jane Austen"
---
```

Chapter ordering is controlled by `chapter_order`, not filename sorting. Keep
`book` and `author` consistent across every chapter in the same book.

`toc_title` overrides the link text shown for a chapter in the book table of
contents. `toc_section` is accepted by the schema but the current book TOC
renders a flat list of chapter links and does not group by section; treat it as
reserved.

## Adding A Book

1. Create `authors/<author-slug>/<book-slug>/`.
2. Add one Markdown file per rendered chapter, usually `chapter-1.md`,
   `chapter-2.md`, and so on.
3. Add `layout: book`, `title`, `chapter_order`, `book`, and `author` front
   matter to every chapter.
4. Put only the chapter body after the front matter. The chapter view renders
   the chapter title automatically.
5. Add the book `index.md` and author `index.md`, or run:

```powershell
python seed_indexes.py
```

`seed_indexes.py` only creates missing index files. It does not split books,
rewrite chapters, or update existing indexes.

## Raw Gutenberg Imports

When importing raw Project Gutenberg HTML, first check whether the title already
exists as a book or as a chapter within an existing book for that author.

Converted works belong under `authors/<author-slug>/<book-slug>/` as a book
`index.md` plus one Markdown file per rendered chapter or section. Strip
Gutenberg boilerplate, generated contents, license text, and HTML navigation.

## Local Development

Requirements:

- Node.js (18.20.8+, 20.3+, or 22+ — Astro 5's supported versions)
- Python, only for `seed_indexes.py`

Install dependencies:

```powershell
npm install
```

Start the dev server:

```powershell
npm run dev
```

Build the site (runs `astro check` for type checking, then `astro build` into
`dist/`):

```powershell
npm run build
```

Preview the built output locally:

```powershell
npm run preview
```

The corpus is large (thousands of chapters), so full builds can take several
minutes.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the
Astro site and publishes `dist/` to GitHub Pages. The repository's Pages source
must be set to **GitHub Actions** (Settings → Pages → Build and deployment). The
custom domain is preserved by `public/CNAME`, which Astro copies into every
build.

## Public Domain Notice

Works hosted here are intended to be public domain in the United States. Users
outside the United States should verify the copyright status in their own
jurisdiction.
