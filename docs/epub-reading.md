# EPUB downloads and export

EPUB downloads are available for A Study in Scarlet and The Chronological
Sherlock Holmes, on their edition pages and the Downloads page. EPUB is a
download format for ebook apps and devices. Online and PDF are the two site
reading modes. The embedded EPUB component, browser script and reading links
have been removed. Old `view=epub` links open online reading in the same edition
and chapter, preserving any explicit interface locale.

## Template

`scripts/export/epub.css` defines the portable reflowable template. The exporter
uses the existing TEI renderer, retaining headings and their hierarchy,
italics, bold, small capitals, letters, block quotations, verse and drama,
tables, source-language attributes and available artwork. Site popovers become
linked EPUB footnotes with backlinks. Source and responsibility statements,
rights, editorial notes, canonical edition URL and the embedded font license
are included in the publication record.

New Computer Modern regular, italic, bold and bold italic are embedded once.
Other scripts can use the ebook application's font fallbacks. Existing approved
image previews are used when available; original documentary figures retain
their source image and caption. No images, portraits, TEI or PDFs are modified.

One `.epub` file serves both themes. The packaged stylesheet supplies light/dark
defaults; downloaded books remain subject to the ebook application's theme
and font settings. Line and page breaks reflow; the PDF remains available when
the reader wants fixed pagination.

## Explicit publication

```powershell
npm run epubs -- doyle_a-study-in-scarlet_eng.xml doyle_the-chronological-sherlock-holmes_eng.xml
```

The command builds EPUB 3 packages under `public/downloads/epub/<author>/`,
with edition filenames, individual manifests and a committed
`src/data/epub-publications.json` snapshot. `--all` can explicitly export the
corpus; it is not part of site deployment. Vite compiles the shared TEI renderer
and its locale catalogues for this offline command. Canonical source checksums
and EPUB checksums are verified by the site build. The pilot files are hosted
with the website; a larger rollout should review its Pages size budget before
deciding whether to use a separate EPUB publication repository.

Validate generated files using [EPUBCheck](https://github.com/w3c/epubcheck),
then run unit tests, build the site and run browser checks. Review actual
exported chapters in an ebook application in both themes, including notes,
verse and illustrations. The deployment copies validated artifacts and never invokes
the EPUB exporter, TEI importer or PDF exporter.

The container follows the [W3C EPUB specification](https://www.w3.org/TR/epub-33/):
an uncompressed first `mimetype` entry, a container document, package metadata,
manifest, reading-order spine and XHTML navigation. Publication checks also
validate local resources, footnote destinations and source hashes.
