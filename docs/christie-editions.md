# Agatha Christie editions

Bookstacks adds the 17 English publications listed by Project Gutenberg on
28 October 2026: 14 books and three standalone periodical stories. The
periodical versions of *The Missing Will* and *The Hunter’s Lodge Case* remain
separate from their versions in *Poirot Investigates*. *The Plymouth Express
Affair* is absent from that collection’s eleven-story UK contents.
*Giants’ Bread*, published as Mary Westmacott, is catalogued under Christie;
the source description identifies the pseudonym.

| Edition | Gutenberg | Reading pages |
| --- | --- | ---: |
| The Mysterious Affair at Styles | [863](https://www.gutenberg.org/ebooks/863) | 13 |
| The Secret Adversary | [1155](https://www.gutenberg.org/ebooks/1155) | 29 |
| The Murder on the Links | [58866](https://www.gutenberg.org/ebooks/58866) | 28 |
| Poirot Investigates | [61262](https://www.gutenberg.org/ebooks/61262) | 11 |
| The Man in the Brown Suit | [61168](https://www.gutenberg.org/ebooks/61168) | 37 |
| The Secret of Chimneys | [65238](https://www.gutenberg.org/ebooks/65238) | 31 |
| The Murder of Roger Ackroyd | [69087](https://www.gutenberg.org/ebooks/69087) | 27 |
| The Big Four | [70114](https://www.gutenberg.org/ebooks/70114) | 18 |
| The Mystery of the Blue Train | [72824](https://www.gutenberg.org/ebooks/72824) | 36 |
| The Seven Dials Mystery | [75288](https://www.gutenberg.org/ebooks/75288) | 34 |
| The Mysterious Mr. Quin | [78084](https://www.gutenberg.org/ebooks/78084) | 12 |
| Murder at the Vicarage | [78220](https://www.gutenberg.org/ebooks/78220) | 32 |
| Partners in Crime | [78342](https://www.gutenberg.org/ebooks/78342) | 23 |
| Giants’ Bread | [78262](https://www.gutenberg.org/ebooks/78262) | 29 |
| The Missing Will | [67173](https://www.gutenberg.org/ebooks/67173) | 1 |
| The Hunter’s Lodge Case | [67160](https://www.gutenberg.org/ebooks/67160) | 1 |
| The Plymouth Express Affair | [66446](https://www.gutenberg.org/ebooks/66446) | 1 |

Gutenberg identifies each source as public domain in the USA. This is the
source edition’s distribution statement, not a claim about every Christie
work or its status in every country. Each TEI header retains the source link,
transcription credits and source file hash. `tei/christie/selection.json`
records the exact downloaded HTML URLs, hashes, source figures and edition
identities. Further Christie titles require an appropriate source edition.

The complete source narratives, emphasis, letters, tables and explicit line
breaks are retained. Printed page-number markers, repeated title pages,
contents tables, publisher advertisements and Gutenberg’s boilerplate are
excluded from the narrative. Author dedications, the *Blue Train* cast and the
*Plymouth Express* periodical introduction appear on their first reading pages.
Original textual diagrams and the periodical’s illustration remain inline;
they are distinct from the new artwork. Source transcriber notes are credited
in the edition descriptions and remain available at the source links.
*Giants’ Bread* retains its prologue, five books, 28 chapters and internal
numbered sections. *Partners in Crime* retains all 23 chapters, including
stories continued across chapters, rather than collapsing those divisions.

There are 363 new AI-generated engraving-style sketches, one per chapter,
prologue or story reading page. Each sits beneath the right-hand chapter
navigation through the existing reader component. The reader supplies the
same monochrome theme treatment and four-edge fade used for Poe and Holmes;
on narrow screens the navigation and artwork stack with the text. The approved
Christie portrait is reused. No interface-language or catalogue-filter logic
changes, and English remains the text’s language independently of the interface.

`tei/christie/illustration-plan.json` records each image’s title and source
excerpt. `art-records/` and `illustrations.json` record exact prompts, built-in
OpenAI image generation credit, generation date, master checksum, delivery
image dimensions and checksum, and preview checksum. The sketches are new
interpretations, not historical plates. Generated PNG masters are cached in
the ignored `assets/source-christie-art/`; JPEG delivery images and smaller
640-pixel previews are committed under `tei/christie/img/`.

The explicit offline importer is `python tei/build_christie.py`. Download the
HTML URLs in the selection manifest to `assets/source-christie/<id>.html`
before running it. It refuses changed source bytes, compares every converted
block’s normalized text with its source, checks the expected section counts
and documentary image hashes, and validates each TEI document against the
schema. `import-report.json` records the per-page block counts and text hashes.
`python tei/prepare_christie_art.py` converts already-generated master images
into delivery files and previews; it does not generate images.

Validation uses `python tei/validate_tei.py tei/christie`, `npm test`,
`npm run build` and `npm run test:browser`. Christie checks cover all edition
counts, distinct illustrations and file hashes, preserved source figures,
English reading routes and the responsive illustrated sidebar. Website builds
and deployment read the committed corpus; they never run the importer, fetch
source texts, generate images or create PDFs. These additions contain no new
PDF publications.
