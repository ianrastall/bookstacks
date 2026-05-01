# Bookstacks Agent Notes

## Repo Shape

- This is a Jekyll static site for public domain texts.
- The site source lives directly in `authors/<author-slug>/<book-slug>/`.
- There is no repo-local `books/` source library, `migrate_books.py`, `books/catalog.json`, or per-book `nav.json` in this version.
- Treat the Markdown files under `authors/` as the source of truth for reading content.
- Shared site chrome and page behavior live in `_layouts/`, `_includes/`, `assets/css/style.css`, and `assets/js/theme.js`.
- Raw Project Gutenberg HTML files may be temporarily dropped into the root of `assets/` for import. They are not long-term site assets.
- Images live under `img/`, usually grouped by author slug.
- `seed_indexes.py` only creates missing author and book index files. It does not split books, rewrite chapter content, or update existing index files.

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

- Place chapters at `authors/<author-slug>/<book-slug>/chapter-N.md`.
- Use lowercase hyphenated slugs. Existing author slugs generally use `surname-given`, for example `austen-jane`.
- Keep `chapter_order` numeric and sequential within a book. The table of contents and chapter navigation sort by this value, not by filename order.
- Keep `book` and `author` values consistent across every chapter in the same book. `seed_indexes.py` uses the most common chapter values when creating a missing book index.
- Use UTF-8 text. Existing content includes typographic punctuation; preserve the style already used by the surrounding text.
- Prefer plain Markdown prose. Do not introduce raw HTML in chapter files unless the layout or existing nearby content requires it.

## Layout Behavior To Remember

- `_layouts/default.html` wraps all pages, includes the header/footer, loads Material Icons, `assets/css/style.css`, and `assets/js/theme.js`.
- `_layouts/author_index.html` lists pages with `layout: book_index` whose URLs fall under the current author page URL.
- `_layouts/book_index.html` lists pages with `layout: book` whose URLs fall under the current book index URL, sorted by `chapter_order`.
- `_layouts/book.html` derives the author slug and book slug from `page.url`, builds breadcrumbs, renders chapter content, and computes previous/next chapter links from sorted `layout: book` pages in the same book.
- Chapter reading styles are under `.reader-content` in `assets/css/style.css`.
- Chapter page layout and sticky right-side chapter navigation use `.chapter-container`, `.chapter-layout`, `.chapter-sidebar`, `.chapter-navigation`, and `.chapter-nav-button`.
- Keep layout changes compatible with the existing dark/light theme variables and responsive breakpoints.

## Converted v0 Concepts

- Old v0 `books/<author>/<book>/<author-book>.html` source files have no equivalent here. Each chapter Markdown file is now the editable source.
- Old v0 `class="navchap"` splitter headings are replaced by one `chapter-*.md` file per rendered chapter.
- Old v0 heading hierarchy rules are replaced by explicit `chapter_order` front matter.
- Old v0 `migrate_books.py` output under `authors/` is replaced by direct edits to `authors/`.
- Old v0 `books/catalog.json` and per-book `nav.json` are replaced by Jekyll pages and Liquid queries over front matter.

## Working Rules

- Do not apply the old v0 workflow. Do not look for `books/<author>/<book>/<author-book>.html` as canonical source in this repo.
- Do not invent a migration or splitting step unless the user explicitly asks for one.
- When fixing text, edit the relevant `authors/.../chapter-*.md` file directly and keep the YAML front matter intact.
- When adding a new book, add all chapter files plus the book index. Add the author index too if it is a new author.
- When importing raw Gutenberg HTML from `assets/`, delete each raw input after it has either been converted into Markdown or identified as a duplicate of existing site content.
- When adding a new author or book and only missing indexes need to be filled in, run `python seed_indexes.py`.
- `seed_indexes.py` is intentionally conservative: it only writes an index file if that file does not already exist.
- Keep unrelated generated/cache output out of commits, especially `.jekyll-cache/` and any local `_site/` output.
- Be careful with broad searches in `authors/`; the corpus is large. Prefer scoped paths when inspecting or editing a specific author or book.

## Raw Gutenberg Assets

- Treat `assets/*.html` and `assets/*.htm` as temporary raw import files. Do not disturb `assets/css/` or `assets/js/`.
- Gutenberg inputs may be copied in blind from old download folders. Always check for duplicates before creating new books.
- Check duplicates by normalized title against existing book slugs and by normalized title against existing chapter titles for the same author.
- If a raw file is a duplicate, remove the raw file and do not create another book directory.
- If a raw file is new, convert it into `authors/<author-slug>/<book-slug>/index.md` plus chapter Markdown files in the current content model.
- Extract the author and title from the source metadata or visible title block, then use the existing author slug if that author is already present.
- Strip Project Gutenberg boilerplate, license text, generated contents pages, transcriber notes, HTML navigation, and other non-reading scaffolding.
- Preserve the work's reading structure. Many Gutenberg files are single stories, but some contain introductory sections, after-story sections, roman-numeral parts, verse, or grouped sketches that should become separate chapter files when they render as separate reading sections.
- After conversion, verify there are no remaining raw Gutenberg markers in the new Markdown and delete the handled raw input file.

## Adding Or Converting A Book

1. Choose slugs and create `authors/<author-slug>/<book-slug>/`.
2. Split the source text into one Markdown file per rendered chapter or section.
3. Name files `chapter-1.md`, `chapter-2.md`, and so on unless there is an existing reason to follow a different local pattern.
4. Add chapter front matter with `layout: book`, `title`, `chapter_order`, `book`, and `author`.
5. Put only the chapter body after the front matter. The chapter layout already renders `page.title` as the chapter heading.
6. Remove Project Gutenberg boilerplate, license text, generated contents pages, navigation scaffolding, and trailing ephemera that is not part of the reading text.
7. Preserve the reading text's paragraphing, verse lineation, emphasis, and notes as plain Markdown wherever possible.
8. Inline or adapt footnotes only when needed for readability, and keep the result in the chapter where the note marker appears.
9. Add `index.md` files for the author and book, or run `python seed_indexes.py` after the chapters are in place.

## Text Editing Guidance

- Preserve public domain reading text unless the task is explicitly to correct it.
- Preserve paragraph boundaries and blank lines in Markdown chapters.
- Preserve emphasis markers already present in the source.
- Do not normalize curly quotes, dashes, accents, or spelling unless the user asks for that specific cleanup.
- Do not remove apparent archaic spelling or punctuation just because it looks unusual.
- If adding images to chapter content, keep paths root-relative or Jekyll-safe and verify they work with `relative_url` expectations in the surrounding layout.

## Verification

- For Liquid/template changes, at minimum parse changed templates with Ruby/Liquid when available:

```powershell
ruby -e "require 'liquid'; Liquid::Template.parse(File.read('_layouts/book.html')); puts 'Liquid parse OK'"
```

- For content-only changes, verify front matter and paths rather than running a full build by default.
- Full `jekyll build` can be slow because the library contains thousands of chapters. Use it when the change affects global layouts, navigation, or site generation, and allow a long timeout.
- A focused temporary Jekyll build with a tiny sample `authors/` tree is acceptable for checking layout behavior quickly.
- After adding or moving chapters, verify:
  - the author index exists at `authors/<author-slug>/index.md`;
  - the book index exists at `authors/<author-slug>/<book-slug>/index.md`;
  - every chapter has `layout: book`;
  - every chapter has a numeric `chapter_order`;
  - chapter orders are unique within the book;
  - every chapter has the intended `book` and `author` front matter;
  - table of contents and previous/next navigation render in the expected order.

## Useful Commands

```powershell
python seed_indexes.py
```

```powershell
jekyll build
```

```powershell
rg -n "layout: book|chapter_order:" authors\<author-slug>\<book-slug>
```
