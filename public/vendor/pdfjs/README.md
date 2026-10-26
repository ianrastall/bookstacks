# PDF.js distribution

Version: 6.4.299 (Mozilla pdf.js release v6.4.299).
Source: https://github.com/mozilla/pdf.js/releases/tag/v6.4.299
Archive: https://github.com/mozilla/pdf.js/releases/download/v6.4.299/pdfjs-6.4.299-dist.zip
License: Apache-2.0; retain LICENSE and notices in upstream files.

The generic distribution is self-hosted here. Source maps and Mozilla's sample
PDF are omitted. viewer.html has a Bookstacks title. The application configures
the viewer before initialization via webviewerloaded; application integration
is in src/scripts/pdf-reader.ts. It supplies the selected edition URL, interface
locale, theme tokens, and page restoration. No external PDF rendering service
or CDN is used. PDF scripting and annotation editing are disabled for this
reading interface; download, print, search, outline, text selection and keyboard
navigation remain provided by PDF.js.

For upgrades, replace the distribution from a pinned Mozilla release, retain
this record and the title change, and rerun the embedded reader browser tests.
