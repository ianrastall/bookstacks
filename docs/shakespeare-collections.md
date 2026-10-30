# Shakespeare language collections

Ian's requirement, 29 October 2026: maintain a complete set of plays in each
language, as distinct files. English is the reference checklist; translations
retain their own translators, text, notes and act/scene structures. The library
remains unified across languages. Incomplete sets remain visible while being
completed; no placeholders or substituted English texts stand in for translations.

## Checklist and current coverage

The [reviewed checklist](../src/data/shakespeare-plays.json) contains the 38
surviving plays in the [Folger list](https://folgerpedia.folger.edu/William_Shakespeare%27s_plays),
including *Pericles* and *The Two Noble Kinsmen*. Every play has a separate
English TEI file and a separate French TEI file. Spanish currently has nine
files, with 29 still to acquire. See the [per-play coverage table](shakespeare-coverage.md).

The 38-play scope is explicit, not a claim that attribution is settled for
every surviving Elizabethan play. *Edward III* is an additional acquisition
candidate: [Gutenberg 1770](https://www.gutenberg.org/ebooks/1770) has the English
text attributed in part to Shakespeare, and [Hugo's French translation](https://fr.wikisource.org/wiki/Édouard_III_(trad._Hugo))
is available. It is not included in the current 38-file sets. Lost plays such
as *Cardenio* cannot be filled with a reconstruction presented as Shakespeare's
surviving original. Poetry is outside this play checklist.

The file convention is `tei/shakespeare/shakespeare_<work>_<language>.xml`,
with `eng`, `fra`, and `spa` filename suffixes and independent `en`, `fr`, and
`es` text metadata. These are complete-work files, not parallel scene fragments.
Existing reading routes and source editions remain intact.

## French completion

The 37 Guizot editions are preserved. The missing *The Two Noble Kinsmen* is
now represented by *Les Deux Nobles Parents*, translated and annotated by
François-Victor Hugo, Paris: Pagnerre, 1866, in *Les Apocryphes*, tome I,
pp. 229–360, with notes on pp. 365–366. The header credits Shakespeare and
John Fletcher as authors and names Wikisource's transcription contributors.
This is a mixed-translator French collection, not 38 Guizot translations.

The [source record](../tei/shakespeare-sources.json) pins the source revision,
scan, history/attribution link and SHA-256 of a committed compressed HTML
snapshot. Transcluded Wikisource scan pages can change independently of the
main page's revision; the committed snapshot makes this import reproducible.
Only the two scan-backed text containers are stored. Website navigation,
decorative images, page markers, invisible layout placeholders and note
backlinks are omitted. Displayed historical wording and transcription
corrections are retained. The source labels the text proofread, pending a
second validation; this import is not a fresh scholarly collation of the scans.

Three print pages were also inspected directly. Two transcription defects were
corrected: `pensée sable` restores the word `irréalisable`, split `irréali-` /
`sable` across pp. 231–232; eight literal wiki indentation colons before
`Le cortége jette des fleurs.` are omitted, and that text is encoded as a
stage direction interrupting the song, as on p. 233. The source record includes
the original and corrected readings and checksums of the three saved scan pages.
These are targeted collations, not a complete scan-by-scan review of the play.

The importer verifies the complete literary character sequence after those
two explicit corrections, source order,
five acts with 5/5/6/3/4 scenes, all 835 source speaker labels, seven verse
passages, prologue, epilogue and three linked notes. French scene divisions
are retained even where they differ from English. XML schema and project
invariants also pass. All 85 Shakespeare files passed schema/invariant checks.

```powershell
python tei/build_wikisource_shakespeare.py --verify-only
python scripts/audit_shakespeare.py
python tei/validate_tei.py tei/shakespeare
```

Run the importer without `--verify-only` only for an explicit source import.
It uses the committed snapshot offline; it never downloads changed text on a
site build. Review and replace the source record and snapshot together for an
intentional source revision. `python scripts/audit_shakespeare.py --write`
refreshes the coverage table. Unit tests require every checklist play in both
English and French, preserving the separate language filenames and reader units.

## Spanish acquisition work

The goal is 38 complete editions, retaining the existing nine rather than
replacing them with an unverified omnibus. Initial checks found only those nine
plays in Gutenberg's [Spanish Shakespeare holdings](https://www.gutenberg.org/browse/languages/es).
The Spanish Wikisource author page is a bibliography, not a collection of 38
available full transcriptions. Several play links are missing, many scan indexes
are marked awaiting transcription, and Clark's *Measure for Measure* transcription
has dialogue and verse collapsed into unformatted paragraphs. These are research
leads, not ready imports.

Next source work should prioritize historical complete collections, preserving
each print source and translator. Macpherson's eight-volume dramatic collection
has [scan indexes linked by Wikisource](https://es.wikisource.org/wiki/Autor:William_Shakespeare),
but its contents do not cover all 38 plays. Martínez Lafuente's and Astrana
Marín's collected translations warrant volume-by-volume source and reuse checks.
Modern reprints and modern revisions must not be treated as identical to the
historical public-domain text. Do not label a scan's raw OCR a finished edition.

For each candidate: establish full-play coverage, source/translator/reuse terms,
inspect the actual text, preserve notes and structural boundaries, validate every
literary block against the source, then publish the distinct TEI and reader.
PDF generation and publication remain explicit, separate operations.

## Publication checks

The new French edition has separately generated 142-page light and dark PDFs,
with identical extracted text and pagination. Cover, publication record, verse,
notes and ending pages were visually inspected. The publication record names
both playwrights, Hugo, the 1866 print source and the recorded transcription.
The exporter now recognizes translation responsibility statements as well as
translator editor elements, retains coauthors, prevents broken cover words and
prints source URLs without French typographic spacing inside the address.
These changes apply to future explicit PDF exports; existing PDFs are preserved.

The PDF publication is maintained in `ianrastall/bookstacks-pdf`.
Hosted PDF checksums are verified after its successful Pages deployment.
The matching website index adds only this edition. Unrelated local PDF edits
were excluded; publication validation checked their committed originals.

Validation includes all 85 Shakespeare TEI files, reproducible snapshot import,
the coverage audit, 63 TypeScript unit tests (including the two new collection
checks), nine PDF-export regression tests, and the 24,911-page Astro build with
no check errors or warnings. All 60 browser checks passed. They cover the French verse and note
links and preserve the French edition when the interface changes to Spanish.
