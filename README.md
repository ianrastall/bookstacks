# Bookstacks

Bookstacks is a Jekyll static site for reading public domain literature at
<https://bookstacks.org>.

The library is organized directly as Markdown source under `authors/`. Jekyll
layouts build the author pages, book tables of contents, and individual chapter
reading pages from that content.

## Project Structure

- `_layouts/`: Jekyll layouts for the default page shell, author indexes, book
  indexes, and chapter pages.
- `_includes/`: shared header and footer markup.
- `assets/css/style.css`: theme, index, table of contents, and reader styles.
- `assets/js/theme.js`: light/dark theme, accent color, and seasonal UI behavior.
- `assets/*.html`: temporary raw Gutenberg import files, removed after they are
  converted or identified as duplicates.
- `authors/<author-slug>/index.md`: author landing pages.
- `authors/<author-slug>/<book-slug>/index.md`: book table of contents pages.
- `authors/<author-slug>/<book-slug>/chapter-N.md`: chapter source files.
- `img/`: image assets, generally grouped by author slug.
- `seed_indexes.py`: utility script for creating missing author and book index
  files from existing chapter front matter.

## Content Model

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

## Adding A Book

1. Create `authors/<author-slug>/<book-slug>/`.
2. Add one Markdown file per rendered chapter, usually `chapter-1.md`,
   `chapter-2.md`, and so on.
3. Add `layout: book`, `title`, `chapter_order`, `book`, and `author` front
   matter to every chapter.
4. Put only the chapter body after the front matter. The chapter layout renders
   the chapter title automatically.
5. Add the book `index.md` and author `index.md`, or run:

```powershell
python seed_indexes.py
```

`seed_indexes.py` only creates missing index files. It does not split books,
rewrite chapters, or update existing indexes.

## Raw Gutenberg Imports

Raw Project Gutenberg HTML can be placed in the root of `assets/` for import.
Before creating new Markdown, check whether the title already exists as a book
or as a chapter within an existing book for that author.

Converted works belong under `authors/<author-slug>/<book-slug>/` as a book
`index.md` plus one Markdown file per rendered chapter or section. Strip
Gutenberg boilerplate, generated contents, license text, and HTML navigation.
After each raw file has been converted or classified as a duplicate, remove it
from `assets/`.

## Local Development

Requirements:

- Ruby
- Jekyll
- Python, only for `seed_indexes.py`

This repo does not currently include a `Gemfile`, so use an environment where
the `jekyll` command is available. The current local setup has been tested with
Jekyll 4.4.1.

Serve locally:

```powershell
jekyll serve
```

Build the site:

```powershell
jekyll build
```

The corpus is large, so full builds can take a while.

## Public Domain Notice

Works hosted here are intended to be public domain in the United States. Users
outside the United States should verify the copyright status in their own
jurisdiction.
