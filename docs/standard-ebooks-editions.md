# Standard Ebooks editions: Father Brown and Lord Peter Wimsey

Added 22 November 2026. Ten English editions are converted from Standard
Ebooks EPUBs: Chesterton's four Father Brown collections, as additional works
under the existing `chesterton-g-k` author, and the first six Lord Peter
Wimsey books, under a new `sayers` author with the approved
`sayers-dorothy.png` portrait.

| Author | Work | First published | Reading units |
| --- | --- | ---: | --- |
| G. K. Chesterton | *The Innocence of Father Brown* | 1911 | Dedication, 12 stories |
| G. K. Chesterton | *The Wisdom of Father Brown* | 1914 | Dedication, 12 stories |
| G. K. Chesterton | *The Incredulity of Father Brown* | 1926 | Dedication, preface, 8 stories |
| G. K. Chesterton | *The Secret of Father Brown* | 1927 | Dedication, 10 stories |
| Dorothy L. Sayers | *Whose Body?* | 1923 | Dedication, 13 chapters |
| Dorothy L. Sayers | *Clouds of Witness* | 1926 | Title page with epigraph, prologue, 19 chapters |
| Dorothy L. Sayers | *Unnatural Death* | 1927 | 3 part openings, 23 chapters, genealogical table |
| Dorothy L. Sayers | *The Unpleasantness at the Bellona Club* | 1928 | Prologue, 23 chapters |
| Dorothy L. Sayers | *Lord Peter Views the Body* | 1928 | 12 stories, crossword solution |
| Dorothy L. Sayers | *Strong Poison* | 1930 | 23 chapters |

## Eligibility

Only works published in 1930 or earlier are included; they are in the United
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
python tei/validate_tei.py tei/chesterton-g-k tei/sayers
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

Source figures (floor plans, maps, crossword grids and the *Unnatural Death*
genealogical table) are copied to `img/` from the high-resolution EPUB images,
flattened onto white so they remain legible in the dark theme. Their source
alternative text is retained. No new illustrations were generated.
