# PDF proof and reader feasibility

The first proof uses the standalone English edition of *A Study in Scarlet*,
`tei/doyle/doyle_a-study-in-scarlet_eng.xml`. Its source is Project Gutenberg
244. This is the original standalone edition, not an extract from either
illustrated Holmes collection. The canonical XML is unchanged.

## Reproduce the proof

Install `requirements-exports.txt` and Tectonic, then run in PowerShell:

```powershell
$env:BOOKSTACKS_EXPORT_ROOT = "$PWD/output/pdf"
python scripts/build_exports.py --file tei/doyle/doyle_a-study-in-scarlet_eng.xml --theme both
```

The PDFs and individual checksum manifests appear below
`output/pdf/doyle/doyle_a-study-in-scarlet_eng/`. The filenames end in
`_eng-light.pdf` and `_eng-dark.pdf`; each has its own `.manifest.json`.
This review directory is outside the site's published downloads. No site build
or deployment invokes the exporter. Use `--theme paper` or `--theme dark`
to generate only one variant. Omit BOOKSTACKS_EXPORT_ROOT to write explicit
offline exports into the publishable `public/downloads/` directory.
The theme participates in the export cache fingerprint.

Both proofs retain the existing 6 × 9-inch format and New Computer Modern
type. The light version has white reading pages; the dark version has warm
dark pages and light text. Both retain the dark cover. Source credits, rights,
edition identity, the editorial footnote and closing verse are preserved.
Contents and PDF bookmarks include both parts and all fourteen chapters.
The exporter now handles nested verse stanzas, which previously disappeared.

## Embedded PDF reader

Reading the PDF within the book page is feasible on the existing static host.
It needs no conversion service or recurring server. Generate and validate
the publication separately, then let the page load that edition's PDF.

The implementation embeds a self-hosted Mozilla PDF.js 6.4.299 viewer in a
same-origin iframe. This is the PDF.js HTML application, not the browser's
native PDF plugin. The user stays at the edition page. Version, license and
upgrade notes live in `public/vendor/pdfjs/README.md`. All viewer resources
are served locally. Source documentation:
<https://mozilla.github.io/pdf.js/getting_started/>.

Implemented behavior:

- Offer Start reading · PDF on the selected edition page when a local PDF exists.
- Retain Download PDF and TEI XML as explicit separate actions.
- Offer both Light PDF and Dark PDF. Use the site's appearance as the initial
  reader preference, allow a separate explicit PDF choice, and preserve the
  page when switching between matching versions. PDF colors are fixed within
  each file; do not simulate dark mode by inverting the light PDF.
- Load the viewer only when selected; retain the existing reader URLs.
- Use same-origin published PDFs first. Release-hosted files need a separate
  CORS check before they can be fetched by PDF.js; a direct Open PDF link is
  the fallback rather than assuming all existing PDF URLs are embeddable.
- Key saved PDF page by the pair's checksums. A regenerated PDF can have
  different pagination. Keep HTML chapter positions separate.
- Keep viewer controls in the interface locale and the book in its edition
  language. Interface changes must not choose another edition.
- Preserve the HTML reader for adjustable text, narrow screens and access
  needs. A fixed PDF page does not inherit HTML font or theme controls.

The standalone Scarlet edition ships with both named PDFs. Existing locally
published PDFs also gain an embedded viewer; older unsuffixed PDFs retain their
original links. The site already supports Light and Dark under Settings >
Appearance > Theme and remembers that choice. The PDF viewer's controls follow
the site's interface locale independently of the edition language. A separate
explicit PDF appearance preference is remembered; otherwise PDF selection
follows the site's theme. Switching variants preserves the current PDF page.
Search, outline, keyboard controls and selectable text come from the full
PDF.js viewer; scripting and annotation editing are disabled for this reader.

EPUB export remains future work. No corpus-wide PDF regeneration is performed.
