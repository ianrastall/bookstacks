# PDF.js distribution

Version: 6.4.299 (Mozilla pdf.js release v6.4.299).
Source: https://github.com/mozilla/pdf.js/releases/tag/v6.4.299
Archive: https://github.com/mozilla/pdf.js/releases/download/v6.4.299/pdfjs-6.4.299-dist.zip
License: Apache-2.0; retain LICENSE and notices in upstream files.

The distribution is self-hosted here. Source maps and Mozilla's sample PDF are
omitted. Bookstacks uses the display API and worker directly from its reading
page, rather than opening the generic viewer. Integration lives in
src/scripts/pdf-reader.ts; the selection layer CSS is adapted from Mozilla's
text-layer rules with its Apache-2.0 attribution. The site supplies page,
contents, search and format controls in its existing reading column.

The generic viewer is retained for older direct links. viewer.html has a
Bookstacks title. The file-origin check in viewer.mjs
also allows `https://ianrastall.github.io/bookstacks-pdf/books/`, the dedicated
Bookstacks publication host, whose PDFs are fetched with CORS. Other external
origins retain Mozilla's rejection behavior. No external PDF rendering service
is used. The direct display API does not initialize the viewer's scripting or
annotation editing application.

For upgrades, replace the distribution from a pinned Mozilla release, retain
this record, the title change and the narrowly scoped origin exception, and
rerun the embedded reader browser tests.
