# Poe illustrated collection

Canonical text: `poe_collected-works-of-mystery-and-horror_eng.xml`.
One English volume: 34 shorter works plus the complete *Arthur Gordon Pym*.

- `selection.json`: contents in reading order, source HTML URLs and SHA-256
  checksums, illustration subjects, accessible descriptions and the seven
  original Pym source-image URLs and checksums.
- `import-report.json`: per-work source block counts and normalized text hashes.
- `illustrations.json`: exact prompts, built-in OpenAI image generation credit,
  dates, dimensions and final PNG checksums for all 36 plates.
- `img/`: all final PNG illustrations. One per shorter work, two for *Pym*.
  Sidebar pages load smaller 640-pixel JPEG derivatives; the full PNGs remain
  the canonical illustrations. `node tei/build_poe_previews.mjs` explicitly
  recreates only those previews and records their hashes in the manifest.
  Seven `pym-source-*.jpg` files preserve the original cave diagrams and glyphs;
  these textual figures remain inline and are distinct from the new artwork.

The images are new AI-generated illustrations in nineteenth-century engraving
style. They are not historical plates. The reader renders them in monochrome,
blends their paper into the active theme, and masks all four edges with soft
gradients. Each reading page displays one plate beneath the right-hand
navigation, outside the prose. On phones it follows the stacked navigation.
Pym uses the voyage plate through chapter 22 and the Antarctic plate for
chapters 23–25 and the concluding note. Existing author portraits are unchanged.

The shorter works come from Gutenberg’s five-volume Raven Edition. David
Widger is credited throughout and Carlo Traverso in volume I. Pym follows
Gutenberg 51060, Ron Swanson’s transcription of the New York 1838 edition,
which includes the cave diagrams and glyphs omitted by the Raven transcription.
Source wording,
emphasis, explicit line breaks, embedded poetry and notes are retained.
The two cipher tables in *The Gold-Bug* retain preformatted line breaks.
Selected notes from the end of volume II are moved after their matching tales.
Pym has its own preface, 25 navigable chapters and original concluding note inside the
same edition. The full selection rationale and author audit are in
`../../docs/author-coverage-and-additions.md`.

Reimport only when deliberately editing this publication:

1. Download each URL in `selection.json` to
   `assets/source-poe/<Gutenberg-number>.html`. Those local sources are ignored
   by Git; the importer refuses any bytes that do not match the pinned hashes.
2. Run `python tei/build_poe.py`. It checks every converted block’s text against
   its source, checks all 25 Pym chapters, and validates the TEI schema.
3. Run `python tei/validate_tei.py tei/poe`, `npm test`, `npm run build`, and
   `npm run test:browser`. The Poe checks cover plate files, chapter navigation,
   source links, the English edition identity and four-sided image masks.

The website build reads committed TEI and images. It never invokes this
importer or creates PDFs. This addition does not include a PDF export.
