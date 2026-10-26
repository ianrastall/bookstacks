# PDF reading and publication

Bookstacks offers two reading modes for every canonical edition:

- **Read online** opens the existing HTML reader with reflow and adjustable text.
- **Read PDF** changes the same chapter reading column to PDF.js, with fixed layout,
  search, outline, text selection and saved physical page position.

The library, author pages, edition pages and chapter controls expose these
choices. Existing HTML chapter URLs, editions, interface locales and source
language metadata remain unchanged. `view=pdf` selects the PDF rendering on
the existing reader route; the online text remains available through its mode
button. The sidebar and site navigation stay in place. PDF pages use the normal
document scroll and column width; there is no iframe, nested application shell
or automatically entered fullscreen view. Existing book-page `#pdf-reader`
links forward to the inline reader without changing the edition.
The embedded PDF follows Settings > Appearance > Theme.
Switching variants preserves the physical page. Saved PDF positions are keyed
by the pair's checksums and kept separate from HTML chapter positions.

## Repositories and hosting

Canonical TEI and the Astro site live in `ianrastall/bookstacks`. Generated
PDFs and publication manifests live in `ianrastall/bookstacks-pdf`, hosted at
`https://ianrastall.github.io/bookstacks-pdf/`. The PDF viewer's application and
display library and worker remain bundled with Bookstacks. Only the PDF bytes come from the
publication host; readers remain at `bookstacks.org`.

This separates the publication set from the main site's Pages size budget.
The publication host exposes the CORS headers needed by PDF.js. The renderer
loads only the edition URLs supplied by the validated publication snapshot.

The site's `src/data/pdf-publications.json` is a committed manifest snapshot.
Each entry identifies the edition through its source filename and SHA-256,
with named light/dark URLs and PDF checksums. A source mismatch fails the site
build. The publication repository's root manifest also records source commit,
canonical edition identity, text language, page counts and extracted-text
checksums. Old supplied PDFs and direct URLs remain available.

## Explicit offline publication

Install Tectonic plus `requirements-exports.txt` and
`requirements-publications.txt`, then run from the source repository:

```powershell
python scripts/setup_pdf_fonts.py
$env:BOOKSTACKS_EXPORT_ROOT = 'D:/jupiter/bookstacks-pdf/books'
python scripts/build_exports.py --all --theme both --workers 4
python scripts/index_pdf_publications.py
python D:/jupiter/bookstacks-pdf/scripts/build_site.py
```

For an individual edition, replace `--all` with
`--file tei/doyle/doyle_a-study-in-scarlet_eng.xml`. Both filenames retain the
normal edition stem and append `-light.pdf` or `-dark.pdf`. Each has its own
checksum manifest. The default exporter theme remains dark; `--theme paper`
generates the light variant alone.

Publish the PDF repository and verify its Pages deployment before publishing
the website's matching manifest snapshot. Neither deployment regenerates TEI
or PDFs. `scripts/export/fonts.json` pins the open font resources by source URL
and checksum; fonts are fetched only for the explicit export pipeline.
The publication repository keeps exporter snapshots and font provenance.

## Validation and scope

The exporter retains the 6 × 9-inch format and New Computer Modern typography,
with Chinese and symbol font fallbacks. Source credits, rights, editorial notes,
verse and available documentary/illustration assets are retained. Images are
sized for the printed page and compressed without modifying their source files.
Unresolvable historical image references retain the canonical figure description;
source acquisition and TEI repair are separate work.

The index command checks all PDF checksums against their manifests, verifies
canonical source checksums, compares every page's extracted text and requires
matching page counts within each light/dark pair. Each PDF must stay below
GitHub's individual file limit, and the publication deployment checks the
aggregate Pages size budget. Representative pages are rendered for visual QA,
including both themes, Chinese, Greek, Cyrillic, notes, verse and illustrations.

The PDF.js distribution, license and upgrade notes are recorded in
`public/vendor/pdfjs/README.md`. Its upstream documentation is at
https://mozilla.github.io/pdf.js/getting_started/.

## EPUB follow-up

EPUB export is separate future work. The intended publication is one reflowable
EPUB package per edition, generated directly from canonical TEI with its source
credits, notes, language and artwork. Its XHTML/CSS can support both site themes;
separate light/dark EPUB files are unnecessary. The embedded EPUB reader should
follow the same site appearance setting and manage contents, saved location and
chapter navigation. Downloaded copies use the ebook application's appearance
controls. PDF remains the fixed-layout option; online reading remains available.
