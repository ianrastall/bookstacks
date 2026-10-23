# Corpus database Stage 1 audit

23 October 2026 · corpus at commit `8a59707` · read-only audit; no TEI, PDF or site files were changed.

This is Stage 1 of [the corpus database plan](../corpus-database-system.md): an inventory of the TEI corpus and of edition metadata held elsewhere, and the evidence for keeping literary text in TEI versus moving it into SQLite. Findings are marked **observed** (measured in the files), **inferred** (a reasonable reading of observations) or **unknown** (needs source review).

## Reproducing the inventory

```sh
py tei/validate_tei.py
py scripts/audit/tei_inventory.py --output docs/corpus-audit/tei-inventory.json
py scripts/audit/metadata_inventory.py --tei-inventory docs/corpus-audit/tei-inventory.json --output docs/corpus-audit/metadata-inventory.json
```

`tei-inventory.json` lists every element, attribute, attribute vocabulary, parent/child pair in `<text>`, language declaration and pointer, plus one record per edition (hash, header fields, features, IDs, unresolved pointers). `metadata-inventory.json` compares those editions with the catalogue data in site code, JSON side files and PDF manifests. Both scripts need `lxml`, which is installed in the `py` (Python 3.14) runtime but not in the `python` 3.12 runtime first on this machine's Git Bash `PATH`; `tei/validate_tei.py` has the same requirement.

## Corpus at a glance (observed)

| Measure | Value |
| --- | --- |
| Editions / works / authors | 257 / 148 / 18 |
| Works with more than one edition | 100 |
| TEI size | 166.6 MB |
| Elements | 974,989 (152 element types) |
| Distinct parent/child pairs inside `<text>` | 387 |
| Distinct element/attribute pairs | 206 |
| Non-whitespace text nodes | 878,298 |
| Elements with mixed content (text and child elements) | 104,641 — mostly `p` (51,828), `said` (36,258), `stage`, `note`, `q` |
| Text nodes whose leading or trailing space sits next to inline markup | 214,098 |
| `xml:id` values | 653,554 (no duplicates within any edition) |
| Local `#` pointers | 160,429 |
| Maximum division depth / element depth | 5 / 14 |
| XML comments | 354 (6 editions have comments inside `<text>`) |
| Most frequent elements | `p` 337,688; `said` 85,809; `l` 75,997; `sp` and `speaker` 70,591 each; `persName` 40,884; `milestone` 38,765 |

Feature spread, by number of editions: verse lines 178; notes 99; named entities 99; milestones 89; foreign-language spans 86; dramatic speech 84; prose `said` 81; attributed speech 80; `q` 74; cast lists 51; editorial interventions (`gap`, `supplied`, `unclear`, `del`, `add`) 46; front matter 27; page breaks 19; editorial `choice` 19; figures 11; tables 9; stand-off registers 7; letters/floating text 7; epigraphs 5; back matter 5; lists 1.

## Validation baseline (observed)

`tei/validate_tei.py` passes all 257 editions: Relax NG against `tei_all.rng`, unique IDs, IDs on divisions, paragraphs, utterances and dramatic structures, and resolvable `who`/`toWhom` on `said` and attributed `q`. It does not check other pointers, attribute vocabularies, language codes or header content. Every finding below exists in files that pass it.

## Findings

### 1. Dangling references (observed; cause partly unknown)

346 local pointers resolve to nothing in their own file.

| Edition(s) | Pointers | What they are |
| --- | --- | --- |
| `tolstoy_resurrection_rus` | 83 `ref/@target` → `#n1`…`#n83` | Note references in the body; the file contains one `note`. The reader shows links to nothing. **Unknown** whether notes were lost in conversion: the Tolstoy Digital source in `D:/dev/proj/bookstacks/assets/works` has two `note` elements and glossary links (`target="slovar"`), so the targets may be a glossary that was never carried over. |
| `tolstoy_childhood-boyhood-youth_rus` | 48 `ref/@target` → `#backn1`… | Same pattern; the file has 113 notes named `source-N-noteM` and no `<back>`. **Unknown** whether these are missing back notes or references that were not renamed when three works were compiled. |
| 7 Dostoevsky Russian editions | 151 `ref`, 1 `source` | Entity references (`#roh`, `#aalv`, `#patronymic` …) to authority entries absent from the file; one `quote/@source` to `#schill`. |
| 7 Dostoevsky Russian editions | 12 `who` | `revisionDesc/change/@who` → `#BB`, `#JT`: undeclared editors from the source project. |
| 6 Tolstoy Russian editions | 42 `ana` | Header `catRef` → undeclared taxonomy categories. |
| `plato_protagoras_eng` | 8 `ana` | Metrical analysis on verse lines (`#met-u`, `#met-dactylic`) without a declared taxonomy. |
| `austen_sense-and-sensibility_eng` | 1 `corresp` | `person` → `#us.004.mrp`. |

### 2. Uncontrolled attribute vocabularies (observed)

Source conventions passed straight through, so equivalent meanings have several spellings and some values are word-processor residue:

- `hi/@rend`: `italic` 21,174; `Italic` 119; `i(1)` 465; `em` 96; `it` 2; `#italic` 1; `itlalic` 1 — plus `sup`/`superscript`, `sc(1)`, `color_-65536` 52, `Razradka` 7, `font_times_new_roman fontsize_18`.
- `q/@type`: `soCalled` 41 and `socalled` 1. `milestone/@unit`: `line` and `Line`. `note/@type`: `Com`.
- Inner `xml:lang` values mix BCP 47 and ISO 639-2/3 codes and include invalid tags: `de` 29 / `deu` 81, `fr` 1,304 / `fre` 96, `la` 50 / `lat` 441, `en` / `eng`, and `engs`, `ft`, `greek`. These values become HTML `lang` attributes in the reader.
- `plato_republic_eng` declares `<text xml:lang="eng">`; every other edition uses BCP 47 on `<text>`.

### 3. Header heterogeneity (observed)

Header shape follows each import source rather than one profile.

- Author names differ within one author: Austen `Austen, Jane, 1775-1817` and `Jane Austen1775–1817`; Dostoevsky `Fedor Dostoevskii` and `Fyodor Dostoyevsky`; Tolstoy `Толстой Лев Николаевич`, `graf Leo Tolstoy`, `Leo Tolstoy`; Turgenev in Latin and Cyrillic; Shakespeare's dates with a hyphen or an en dash. (Where a name runs into dates above, the header holds the dates in a separate child element.)
- Placeholder elements: the six English Austen headers contain 14–240 empty elements each (empty `note`, `correction`, `normalization`, `term`); three Dostoevsky headers have a few.
- Gaps: no `langUsage` in the six English Austen editions; no `publicationStmt/idno` in the three Chinese editions; `sourceDesc` has no `bibl` in 116 editions and no source URL in 134; `editorialDecl` exists in 14; the typed source-description note the reader displays exists in 3.
- Translator or editor credit (a `respStmt` other than the Bookstacks encoding statement, or `editor`) is absent in 60 editions. **Inferred:** some are originals that need none; which translations lack credit needs review.

### 4. Catalogue identity lives outside TEI (observed)

- A **work** exists only as the middle segment of file names. No TEI file records which work it belongs to or which editions are its translations.
- Work titles: 85 come from `WORK_TITLES` in `src/lib/library.ts`; the other 63 of 148 are generated from the slug.
- Author display names, dates, portraits and descriptions come from `src/data/author-profiles.json` (18 entries), not from the headers in finding 3.
- Language: the file suffix (`eng`, `zho` …) is mapped to a route code by `LANGUAGE_DATA` in `library.ts`; the TEI declarations are not used for routing.
- Old author URLs are redirected from `astro.config.mjs` (4 entries).
- Reading-unit rules (`READING_KIND_PRIORITY`, `SUPPLEMENTARY_KINDS`, `WRAPPER_KINDS`) and a render-time repair of the French Shakespeare files (`repairConvertedDrama`) are code, not edition data.

### 5. Publication records cannot be checked against their TEI (observed)

- 240 editions have a committed PDF and `manifest.json` under `public/downloads/`; their PDF hashes match and their canonical URLs match current routes.
- No manifest records the hash of the TEI it was made from, so whether a PDF reflects the current TEI cannot be determined. **Inferred:** probably current, since the PDFs were committed on 27 August after every TEI change except Conan Doyle and the Chinese editions.
- 17 editions have no PDF anywhere: 14 Conan Doyle and the 3 Chinese editions.
- The same PDFs are also published as 212 assets in six `publications-*` releases, a second copy with no recorded relationship to the first.

### 6. Provenance is recorded unevenly (observed)

Only the Chinese editions have a machine-readable source register (`tei/chinese-sources.json`: URL, Wikisource revision, content hash). Plato and Aristotle source paths are in `tei/tei_build_config.json`, pointing at ignored files under `assets/`. Other provenance is prose in `tei/README.md` and `sourceDesc`. The raw sources are not in this checkout; some are in `D:/dev/proj/bookstacks/assets`.

### 7. Reader coverage (observed)

The reader renders 64 element types explicitly; 22 other types inside `<text>` fall back to their children's text: title-page parts (`titlePage`, `docTitle`, `titlePart`, `docAuthor`, `docImprint`, `docDate`, `docEdition`, `byline`), `list`/`item`, `cit`, `writing`, `num`, `supplied`, `publisher`, `pubPlace` and structural containers. No text is dropped, but list, citation and title-page structure is not shown.

## What this means for the storage decision

### Evidence for keeping literary text in TEI

- **Every defect found is a consistency or completeness problem in valid XML, not something XML could not represent.** Dangling pointers, vocabulary drift, invalid language codes, header gaps and missing work identity can all be caught by validator rules and recorded in a catalogue without changing where text lives.
- **The text is deeply mixed.** 104,641 mixed-content elements, 214,098 whitespace-significant text nodes, 387 nesting combinations and 653,554 public IDs would become roughly 1.85 million ordered node rows (elements plus text nodes), each needing exact order, whitespace, namespace and ID scope to export back to equivalent TEI. That round trip is the costliest and riskiest part of the plan, and it would fix none of the findings above.
- **Text changes arrive in bulk from importers.** Only 20 of 201 commits touch `tei/`, each a source import or re-conversion. No passage-level hand editing was observed that a database would make safer. Text-file diffs show these changes now.
- **TEI is the format the Library of Congress prefers for textual works.** Its SQLite preference applies to datasets.

### Evidence for SQLite

- **Catalogue and publication facts are scattered with no constraints.** Work identity, titles, author identity, language mapping, provenance and publication records sit in at least eight places: file names, `WORK_TITLES`, `LANGUAGE_DATA`, `author-profiles.json`, `astro.config.mjs`, PDF manifests, the release index, `chinese-sources.json` and `tei_build_config.json`. Questions such as "which editions have no PDF" or "which PDFs predate their TEI" need ad hoc scripts today; with foreign keys and hashes they are queries.
- **Assessments and reviews have no home.** "No notes in source" versus "notes not checked" cannot be recorded in TEI without inventing markup. Findings 1 and 2 are exactly what a feature assessment would track.
- **Search.** A full-text index (FTS5 or a static derivative) is naturally derived data keyed by edition hash and `xml:id`.

### What would justify moving text into SQLite later (not observed)

Passage-level editing by people with per-change review; evidence-backed cross-edition alignment at paragraph level; or requirements that schema plus rule validation demonstrably cannot express. None of these is present now.

## Recommendation

Keep TEI XML as the authority for literary text. Make SQLite the authority for the records around it, each pointing into TEI by file, SHA-256 and `xml:id`:

| Record | Replaces |
| --- | --- |
| Work, edition (file, hash, language, route), work–edition membership | File-name parsing, `WORK_TITLES`, `LANGUAGE_DATA`, route redirects |
| Contributor and credit (author, translator, editor; preferred and source forms) | `author-profiles.json`, inconsistent header names |
| Source and source use (URL, revision, content hash, scope) | `chinese-sources.json`, `tei_build_config.json`, README prose |
| Feature assessment and review (scope, evidence, assessor, revision hash) | Nothing today |
| Release and artifact (edition hash, exporter version, artifact hashes, location) | PDF manifests, release index |
| Validation result (rule, edition hash, outcome) | Console output only |

Independently of storage, extend `tei/validate_tei.py` with a versioned Bookstacks profile: every local pointer resolves to an allowed target type; `rend`, `type`, `unit` and `place` values come from declared lists; `xml:lang` values are valid BCP 47; required header fields are present and non-empty. Run it as a report first, because it will fail the findings above until they are resolved.

## Representative fixtures for Stage 2

| Fixture | Why |
| --- | --- |
| `austen/austen_emma_eng.xml` | `particDesc`, attributed `said`, header placeholders, missing `langUsage` |
| `austen/austen_emma_spa.xml` | EPUB-derived front/back matter, page milestones, independent translation |
| `shakespeare/shakespeare_hamlet_eng.xml` and `shakespeare_alls-well-that-ends-well_fra.xml` | Drama, verse and prose speech; the French files depend on `repairConvertedDrama` |
| `dostoevsky/dostoevsky_demons_rus.xml` | Stand-off registers, multi-party pointers, unresolved authority refs, suppressed chapter |
| `tolstoy/tolstoy_resurrection_rus.xml` | 83 dangling note references |
| `tolstoy/tolstoy_childhood-boyhood-youth_rus.xml` | Compiled from three works; `choice/reg/orig`; dangling back-note references |
| `plato/plato_republic_grc.xml` and `plato_republic_eng.xml` | Stephanus milestones; ISO 639-3 text language in the English edition |
| `aristotle/aristotle_poetics_eng.xml` | Notes and Bekker milestones used by the reader tests |
| `doyle/doyle_the-return-of-sherlock-holmes_eng.xml` | Figures and graphics; no PDF |
| `lu-xun/lu-xun_call-to-arms_zho.xml` | Chinese structure, source register, missing `idno`, no PDF |

## Decisions for Ian

1. **Storage boundary.** Adopt the hybrid above, or continue toward text in SQLite? This audit found no evidence that requires the latter.
2. **Dangling Tolstoy notes.** Investigate against the Tolstoy Digital sources before any migration (131 references across two editions)?
3. **Normalizing vocabularies.** Rewriting `rend` and language codes changes TEI. Normalize in the files, or keep source values and map them in the profile? `Razradka` (Russian letter-spacing) and the colour value carry source meaning that a blind rewrite would lose.
4. **Author name forms.** Keep each source's form in TEI and record a preferred form in the catalogue, or normalize headers?
5. **PDF authority.** Which copy is canonical, `public/downloads/` or the `publications-*` releases, and should future manifests record the source TEI hash?

## Next step

Ian chose the hybrid boundary on 23 October 2026; the Stage 2 prototype is in [`corpusdb/`](../../corpusdb/README.md). The original plan for this step read: with the boundary decided, Stage 2 can be an additive prototype in a new path: a SQLite schema for the records above, populated from TEI and the side files by a read-only importer, plus the profile checks above as a report. The current TEI, site build and deployment stay untouched.
