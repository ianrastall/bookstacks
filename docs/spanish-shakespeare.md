# Spanish Shakespeare additions, 30 October 2026

The Spanish shelf now contains 11 of the [38 checklist plays](shakespeare-coverage.md).
The existing nine editions remain unchanged. Two separate complete-play files
have been added from the Universitat de València's EMOTHE digital editions:

| Work | Translation | Digital source | Acts / scenes |
| --- | --- | --- | --- |
| *El Rey Lear* | Cipriano Montoliu; Barcelona: Miguel Seguí, 1908, vol. 1, pp. 166–244 | [EMOTHE0647](https://emothe.uv.es/biblioteca/textosEMOTHE/EMOTHE0647_ElReyLear.php), encoded by Jesús Tronch Pérez | 5 / 26 |
| *Ricardo III* | John D. Sanderson; *La tragedia del rey Ricardo III*, Alicante: Aguaclara, 1998 | [EMOTHE0703](https://emothe.uv.es/biblioteca/textosEMOTHE/EMOTHE0703_RicardoIii.php), encoded by David J. Amelang | 5 / 25 |

These editions are distributed under the source's **CC BY-NC-ND 4.0** licence,
not represented as public-domain transcriptions. The licence and original
availability statement are retained in each TEI header. Book pages and PDF
publication records identify the source, contributors and reuse terms.
[Section 2(a)(4)](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en#s2a4)
permits technical format changes. Bookstacks changes encoding and structural
markup for its readers, without revising, abridging or translating the text.
The website's software licence does not replace the editions' licence.

Montoliu's digital edition retains EMOTHE's prior spelling modernization and
its credit to Rosa Durá Celma. Sanderson's edition retains its editorial note
explaining the parentheses marking omissions for John Strasberg's 1998 staging;
the parenthesized words remain present. Neither text is reconstructed from OCR.
The original wordings, including source transcription defects, are preserved.
These are conversion checks, not a new collation against printed editions.

The [source manifest](../tei/emothe-shakespeare-sources.json) pins upstream
commit `0a965a5a7eed95e20d19e5608776bc1153bbe5eb`, each original XML checksum,
and its compressed committed snapshot. Import runs entirely offline:

```powershell
python tei/build_emothe_shakespeare.py
python tei/build_emothe_shakespeare.py --verify-only
python tei/validate_tei.py tei/shakespeare
python scripts/index_drama_layout.py
python scripts/audit_shakespeare.py --write
```

The importer verifies every literary character and its order after whitespace
normalization, as well as speech, paragraph, direction, verse, cast and inline
boundaries. It checks all 2,145 speeches, 619 stage directions, 103 verse lines,
five acts per play and the source's independent scene divisions. Existing IDs
and character pointers remain; missing IDs and navigation scene numbers are
added. `div1` and `div2` become `div`; the two front-matter division types map
to the reader's publication-note and characters units. Analytical cast entries
marked `ana="oculto"` remain in the TEI and character index, but follow the
source's non-display convention in both HTML and PDF.

The shared Shakespeare rules render entrances centered, exits right-aligned,
and directions within a character's part inline. The original TEI remains
unchanged by presentation. Light and dark PDFs are generated and published
explicitly; site builds do not run an importer or PDF exporter.

Twenty-seven Spanish plays remain pending. Murcia's historical Clark and
Macpherson collections provide additional scan leads; several Wikisource
links are bibliographic records or unfinished transcriptions. Those leads
are not counted as acquired editions. No English stand-ins are published.

Validation: all 87 Shakespeare TEI files pass schema and project checks; both
offline imports reproduce byte for byte. All 70 site unit tests, 17 Python
layout/export tests and 66 browser tests pass. The Astro production build has
zero diagnostics, and the dependency audit reports no vulnerabilities. Browser
checks include a French interface over each Spanish edition and a 320-pixel
reader. PDF review covers source records, title/cast matter, opening scenes
and endings. The final light/dark pairs contain identical extracted text and
pagination: 158 pages for *El Rey Lear*, 154 for *Ricardo III*. Both dark PDFs
pass the text-object contrast check. The PDF host validates 562 PDFs for 281
editions; no existing publication pair is replaced.
