# Standard Ebooks editions: Father Brown, Lord Peter Wimsey and Wilkie Collins

Added 22 November 2026. Eighteen English editions are converted from Standard
Ebooks EPUBs: Chesterton's four Father Brown collections, as additional works
under the existing `chesterton-g-k` author; the first six Lord Peter Wimsey
books, under a new `sayers` author with the approved `sayers-dorothy.png`
portrait; and the eight Wilkie Collins novels Standard Ebooks publishes, under
a new `collins` author. No Collins portrait was supplied, so his author page
uses the standard monogram until an approved portrait is added.

| Author | Work | First published | Reading units |
| --- | --- | ---: | --- |
| G. K. Chesterton | *The Innocence of Father Brown* | 1911 | Dedication, 12 stories |
| G. K. Chesterton | *The Wisdom of Father Brown* | 1914 | Dedication, 12 stories |
| G. K. Chesterton | *The Incredulity of Father Brown* | 1926 | Dedication, preface, 8 stories |
| G. K. Chesterton | *The Secret of Father Brown* | 1927 | Dedication, 10 stories |
| Dorothy L. Sayers | *Whose Body?* | 1923 | Dedication, 13 chapters |
| Dorothy L. Sayers | *Clouds of Witness* | 1926 | Title page with epigraph, prologue, 19 chapters |
| Dorothy L. Sayers | *Unnatural Death* | 1927 | 23 chapters in 3 parts, genealogical table |
| Dorothy L. Sayers | *The Unpleasantness at the Bellona Club* | 1928 | Prologue, 23 chapters |
| Dorothy L. Sayers | *Lord Peter Views the Body* | 1928 | 12 stories, crossword solution |
| Dorothy L. Sayers | *Strong Poison* | 1930 | 23 chapters |
| Wilkie Collins | *Basil* | 1852 | Letter of dedication, 27 chapters in 3 parts, journal, letters in conclusion |
| Wilkie Collins | *The Dead Secret* | 1857 | 29 chapters in 6 books |
| Wilkie Collins | *The Woman in White* | 1860 | Dedication, preface, 62 chapters in narratives within 3 epochs |
| Wilkie Collins | *No Name* | 1862 | Dedication, preface, 113 chapters in 8 scenes and 7 “Between the Scenes” |
| Wilkie Collins | *The Moonstone* | 1868 | Prologue, 52 chapters and narratives in 2 periods, 3-chapter epilogue |
| Wilkie Collins | *Man and Wife* | 1870 | 2-chapter prologue, 57 chapters in 16 scenes, 2-chapter epilogue |
| Wilkie Collins | *The Law and the Lady* | 1875 | Note to the reader, 50 chapters in 2 parts |
| Wilkie Collins | *The Haunted Hotel* | 1878 | Dedication, 28 chapters in 4 parts, postscript |

## Eligibility

Collins (1824–1889) is in the public domain worldwide. For Chesterton and
Sayers, only works published in 1930 or earlier are included; they are in the United
States public domain. *The Scandal of Father Brown* (1935) and Sayers's later
novels are not imported. *The Five Red Herrings* (1931) becomes eligible on
1 January 2027. Sayers died in 1957, so her works remain in copyright in
countries that use a life-plus-70-years term until 1 January 2028; the TEI
availability statement records this. Standard Ebooks dedicates its own
contributions to the public domain under CC0.

## Sources and conversion

`tei/standard-ebooks-sources.json` pins each EPUB URL and SHA-256. The importer
refuses a changed file. Each TEI header retains the Standard Ebooks page, the
transcription sources it cites (Project Gutenberg, Faded Page, Internet
Archive, HathiTrust or Google Books scans), transcribers and producers.

```powershell
python tei/build_standard_ebooks.py --download
python tei/validate_tei.py tei/chesterton-g-k tei/sayers tei/collins
```

The cache lives in ignored `assets/source-standard-ebooks`. Name work slugs to
rebuild only those editions. The command is offline and explicit; site
deployment does not run it and it creates no PDFs or EPUBs.

The conversion keeps stories, parts, chapters, dedications, prefaces,
prologues, epigraphs, letters, verse with source indentation, tables,
footnotes, scene breaks and inline italics and small capitals. Standard Ebooks
title pages, imprints, tables of contents, colophons and licence pages are
omitted. Chapter headings combine the source numeral and title (for example
“Chapter I. Of His Malice Aforethought”); untitled dedications, prefaces and
prologues receive the conventional English label. The importer compares every
converted character of text and footnote content against the source and stops
on any difference.

Nesting follows the Standard Ebooks `data-parent` links, so chapters sit inside
their parts, books, scenes, epochs and narratives (`div type="narrative"`; a
narrative without chapters of its own is read as a chapter). Chapter numbers
come from the source numerals, so they restart where Collins restarts them.
Subchapters stay on their chapter's page under numbered subheadings, because a
chapter can resume after them (*Man and Wife*, chapter LIV). Place and narrator
lines under headings are centred italic paragraphs. A part's own text, such as
a part epigraph or narrator line, is shown at the start of its first chapter.
Standard Ebooks marks word joiners with the deprecated U+FEFF; the importer
writes the equivalent U+2060.

*Unnatural Death* was first published on 22 November 2026 with its chapters
beside, rather than inside, its parts. Its old chapter and part URLs redirect to
the nested ones (`astro.config.mjs`).

Source figures (floor plans, maps, crossword grids and the *Unnatural Death*
genealogical table) are copied to `img/` from the high-resolution EPUB images,
flattened onto white so they remain legible in the dark theme. Their source
alternative text is retained. *The Law and the Lady* keeps its two signature
facsimiles. No new illustrations were generated.

## Downloads

All eighteen editions have light and dark PDFs in `bookstacks-pdf` and an EPUB
under `public/downloads/epub/`, built with the normal explicit commands
(`scripts/build_exports.py --file …`, `scripts/index_pdf_publications.py`,
`npm run epubs -- …`). The PDF exporter sets Unicode superscript and subscript
digits, used in two Sayers fractions (“⁷⁄₆”, “¹⁄₃₆₂₁”), as LaTeX superscripts and
subscripts because the text font lacks those glyphs.
