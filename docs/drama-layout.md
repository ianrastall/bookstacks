# Shakespeare layout

Ian confirmed these rules on 29 October 2026 for both the online reader and PDF
editions:

- Entrances are centered and enclosed in square brackets. Direction text is
  italic; character names are upright uppercase.
- Exits are right-aligned, with italic direction text and upright uppercase
  character names. They use the same square-bracket convention.
- Directions belonging to a character stay inline in that character's part,
  including directions before the first words or after the last words.

The rules apply to all 85 current Shakespeare editions: 38 English, 38 French
and nine Spanish. Character labels are collected separately for each edition;
one language's names or scene divisions are never substituted for another's.

## Presentation and source boundaries

Canonical TEI, source credits, notes, language identities, reader routes and
approved artwork remain unchanged. The formatters work in a transient DOM/tree.
They normalize existing outer parentheses/brackets to one pair of square
brackets, and remove a separator comma from a direction originally attached to
a speaker label. They do not paraphrase literary text.

Explicit entrance/exit metadata is retained. Shared, conservative movement
patterns also recognize common imported cues such as `Puck revient`,
`Ils sortent`, and `Vase ORLANDO`. Translator-note prose is excluded from cue
classification. An imported block joining an exit and entrance with a blank
line is split into separate display cues, preserving its words and order.

Directions already inside a speech are merged into that speech's prose or
verse. A singular action immediately following its speaker's part stays with
that part. Ensemble or unattributed scene actions keep their source position;
the formatter does not invent a character attribution or move words across
another speech. These source annotations still warrant editorial review where
the importer did not distinguish movement from other business.

The site uses `src/lib/drama.ts`; the explicit PDF exporter uses
`scripts/drama_layout.py`. Both consume the same movement patterns and the
source-pinned character labels in `src/data/drama-layout-rules.json` and
`src/data/drama-layout-index.json`. Stage markup containing a whole sentence
marked as a name no longer forces the whole sentence into upright uppercase.
Inline notes and source references are preserved.

After an explicit new or corrected Shakespeare TEI import, refresh the derived
character index before checking the site or exporting PDFs:

```powershell
python scripts/index_drama_layout.py
```

The source checksum guard rejects an outdated index. Site deployment does not
run this indexing command, import TEI, or generate PDFs. EPUB CSS includes the
same presentation styles for future explicit EPUB exports.

## Verification and publication

Shared English, French and Spanish cue fixtures exercise both formatters.
Checks cover centered entrances, right-aligned exits, one square-bracket pair,
italic surrounding words, upright uppercase names, inline speech directions,
joined imported cues and preserved note links. A full-corpus check compares
the entire character sequence and order before/after preparation, ignoring
whitespace, for all 85 editions.

Browser checks cover English and French movement cues, the Hugo edition's
speech directions, Spanish introductions, and a 320-pixel viewport. PDF samples
are rendered for visual inspection, and each published light/dark pair must
have identical extracted text and page counts.

PDFs are generated in `tmp/drama-pdf-staging/books`. The PDF publication is
assembled in the isolated `tmp/drama-publication` checkout, preserving local
edits in the main `bookstacks-pdf` working directory. The Shakespeare PDFs and
the 17 previously missing Christie pairs are updated, together with their
publication manifests. Verify that
repository's Pages deployment before publishing the website's matching index.

The final PDF pass also restores the theme foreground explicitly after notes
and at speech/paragraph boundaries. This prevents TeX color state from leaving
black text on dark pages. `scripts/check_pdf_contrast.py` inspects PDF text
objects across the newly generated dark editions; it excludes images and
invisible text. Catalogue publication additionally verifies source checksums,
PDF checksums, page counts, and equal extracted text for every light/dark pair.

Final checks: 68 site unit tests and 16 Python layout/export tests passed.
All 102 newly generated dark editions passed the text-object contrast check.
All 279 catalogue pairs (558 PDFs) passed publication validation.
The final website build produced 24,911 pages with zero diagnostics; all 64
browser checks passed, including actual right-edge cue geometry at 320 pixels.
