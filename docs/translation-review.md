# Translation review

First pass: 29 October 2026. Input: Ian's local GA4 Pages and screens CSV,
1–28 October 2026. The report is evidence of visits, not evidence that a
translation is wrong or that engagement represents reading.

## Existing workflow

Follow-up: the [Shakespeare collection record](shakespeare-collections.md)
supersedes this first pass's acquisition status. The French set now contains
all 38 checklist plays; Spanish remains incomplete. Counts below describe the
initial review before that addition.

Literary translations are imported from identified editions into separate
canonical TEI files. They retain their translators, source hierarchies, notes,
language identities and reader routes. This differs from translating interface
controls, whose catalogues are in `src/i18n/locales/`.

There are 278 TEI editions: 163 English, 40 Ancient Greek, 37 French,
20 Russian, 15 Spanish and three Simplified Chinese. Shakespeare has 38
English, 37 French and nine Spanish plays. Austen has six English and six
Spanish novels. Counts describe files, not independent translation versions
within a language; the current route model supports one edition per work/language.

The previous English translation acquisition added Legge's *Tao Te Ching*.
The two other Chinese works remain pending as recorded in
[Chinese English sources](chinese-english-sources.md). No new literary
translation is imported in this first review.

## Findings and changes

- The visited French *Richard II*, act III scene III, is Guizot's translation
  from [Gutenberg 21277](https://www.gutenberg.org/ebooks/21277).
  Comparison with the [source HTML](https://www.gutenberg.org/cache/epub/21277/pg21277-images.html)
  found the same literary words and the translator's note. This is a targeted
  comparison, not native-speaker review or collation of all 37 French plays.
- The old converter split two parenthesized directions into fictitious
  speakers `(L` and `(F`. The existing reader reassembled the words, but lost
  the `.--` punctuation between the reconstructed prefix and the remainder.
  Those two separators are now restored in the display DOM, using the exact
  edition and speech IDs. Canonical XML and independently published PDFs
  remain unchanged. The importer now rejects parenthesized text as a speech
  prefix, preserving the whole direction on future explicit imports.
- Older TEI headers contained translation credits that book pages did not
  display. Book pages now show editor/translator and source responsibility
  statements, source description paragraphs where available, and source
  references. Gutenberg identifiers recorded as prose produce direct source
  links. Credits are transcribed, not inferred: Spanish *Sense and Sensibility*
  remains credited `Anónima`, and English *Theaetetus* names Harold North Fowler.
- Browser language silently selected a book-language filter. The catalogue
  now defaults to all edition languages. Explicit filters remain available;
  interface changes preserve the selected edition and chapter.
- The 168 Shakespeare, Austen and Plato TEI files passed schema and project
  invariant validation. A scan of all 278 files found no replacement characters
  or the checked common UTF-8 mojibake sequences. Every French and Spanish
  file has a header responsibility/editor credit. These checks do not establish
  textual completeness or translation quality.

## Acquisition queue

1. Continue source comparisons for visited French *King John*, *Much Ado About
   Nothing*, *Julius Caesar* (including the independently numbered French act
   II scenes IV–V) and *Measure for Measure*. Preserve edition-specific scene
   divisions rather than assuming English alignment.
2. Expand Spanish Shakespeare around the existing shelf, selecting complete
   historical translations with named or explicitly anonymous attribution,
   inspectable reuse terms, and notes. *Richard II* is a useful candidate,
   but a downloadable copy or author index alone is not an approved source.
   [Educ.ar's listing](https://www.educ.ar/recursos/153037/ricardo-ii%2C-de-william-shakespeare)
   identifies a BY-NC-SA resource and does not name a translator; it has not
   been approved for import. Wikisource's
   [1879 anthology](https://es.wikisource.org/wiki/Pensamientos%2C_m%C3%A1ximas%2C_aforismos_y_definiciones/Historias)
   contains excerpts, not a complete play.
3. French *The Two Noble Kinsmen* is the single French gap in our Shakespeare
   shelf. A suitable complete reusable source has not yet been established.
   The [BnF Ritz record](https://catalogue.bnf.fr/ark:/12148/cb34684124v)
   describes a 1982 translation; it is bibliographic evidence, not reuse
   permission. Do not invent a Guizot edition to fill the gap.
   **Resolved in the follow-up:** Hugo's 1866 complete translation was found
   and imported with its own attribution, structure and notes; see the
   collection record above.

For each acquisition, pin the reviewed source and provenance, verify all
literary blocks/notes and structural boundaries, validate TEI, then check its
reader and edition links. Publish XML and PDFs through their separate explicit
pipelines. A site deployment must not run either acquisition or PDF generation.

## Verification commands

Completed: unit tests, the two importer regression tests, the Astro check/build
(24,853 pages, no check errors or warnings), dependency audit (no reported
vulnerabilities), and all 41 browser checks in the two suites below. The final
library unit suite was rerun after the targeted punctuation correction.

```powershell
python tei/validate_tei.py tei/shakespeare tei/austen tei/plato
python tests/test_french_drama.py
npm test
npm run build
npx playwright test tests/translation-review.spec.ts tests/library.spec.ts
```
