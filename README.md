# Bookstacks

Bookstacks is a statically generated reading site for complete books encoded as TEI P5. Each XML file in `tei/` is a standalone work and language edition; related editions are grouped at the work level without assuming chapter-by-chapter alignment.

See [the Jupiter interface and migration record](docs/jupiter-web.md) for the library/reader redesign and preserved publication boundaries.

## Development

```sh
npm ci
npm run dev
```

Use `npm run build` for the same type check and static production build used before deployment. The generated site is written to `dist/`.

## Edition downloads

Bookstacks distributes only the canonical TEI source and, when supplied, a PDF. The site build does not generate publication files. Every TEI file under `tei/<author>/` is downloadable from its book page and the downloads index.

To publish a PDF, commit it beside its matching TEI file with the same basename:

```sh
tei/austen/austen_emma_eng.xml
tei/austen/austen_emma_eng.pdf
```

PDF links resolve in this order:

1. a PDF committed beside its TEI file under `tei/<author>/`;
2. exporter output committed under `public/downloads/<author>/<edition>/<edition>.pdf` (the current source of most published PDFs, served at `/downloads/...`);
3. a matching asset in a `publications-*` GitHub release, indexed by `scripts/index_release_pdfs.mjs` before the deployment build.

The site build and deployment never regenerate the corpus or PDFs. `scripts/build_exports.py` remains available for explicitly invoked local PDF creation; neither `npm run build` nor the deployment workflow runs it, and its output is published only when it is committed.

## Languages

Bookstacks keeps two kinds of language separate.

- **Edition language** is the language of a literary text: English, French, Spanish, Ancient Greek, Russian or Simplified Chinese. Reading routes begin with it (`/fr/authors/...`). It is edition metadata and an optional catalogue filter.
- **Interface language** is the language of the site's controls. Forty interface locales are available: Arabic, Bengali, Czech, Danish, German, Modern Greek, English, Spanish, Persian, Finnish, Filipino, French, Ancient Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Marathi, Malay, Norwegian Bokmål, Dutch, Polish, Portuguese (Brazil and Portugal), Romanian, Russian, Swedish, Swahili, Tamil, Telugu, Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Simplified and Traditional Chinese.

The interface follows the browser's language preferences in order, falling back to English. The labeled selector offers a manual choice that is saved in the browser; `?ui=<locale>` applies a shareable override and `?ui=auto` clears it. Changing the interface language never changes the catalogue filter, selected edition, chapter or reading position. On the first catalogue visit, the book-language filter follows the first matching browser language preference; if none matches an available edition language, it shows all languages. The filter remains explicit in the URL (`language=all` preserves All languages). Books per page offers 16, 32, 64 or all editions, remembers the choice locally and supports a `size` URL parameter. Arabic, Hebrew, Persian and Urdu interfaces set `dir="rtl"`; edition text keeps its own `lang` and `dir`. Static catalogue pages at `/<locale>` (for example `/de`) serve browsers without JavaScript.

Interface text lives in `src/i18n/locales/<locale>.ts`, one catalogue per locale, typed against the English catalogue in `en.ts`. Counts use CLDR plural categories through `Intl.PluralRules`. The browser loads only the catalogue it needs. To add a locale, add it to `INTERFACE_LOCALES` in `src/lib/i18n.ts` and create its catalogue; `npm test` checks that every catalogue has every message and placeholder. The translations other than English, French, Spanish, Ancient Greek, Russian and Simplified Chinese were added on 23 October 2026 without native-speaker review; corrections are welcome.

The Simplified Chinese editions are Lu Xun’s *Call to Arms* (preface and 14
stories), *Journey to the West* (100 chapters), and *Tao Te Ching* (81
chapters). Their contents and reading typography follow the edition language.
Book pages identify the selected text sources and character conversion. The
Chinese authors have engraved illustration portraits matching the existing
shelf. Lu Xun follows his documented photographic appearance; Wu Cheng’en and
Laozi use traditional artistic representations, identified in the image
descriptions. Generation prompts are recorded in
`public/img/authors/chinese-portraits.md`. Author cards use character monograms
where no portrait has been supplied.

The English *Tao Te Ching* edition contains James Legge’s complete translation from Project Gutenberg ebook 216, with both parts, all 81 chapters and verse preserved. Complete freely reusable English editions of *Call to Arms* and *Journey to the West* still need suitable sources; see [the translation source record](docs/chinese-english-sources.md).

Reader controls adjust text width (32–100 rem), text size and serif/sans-serif cascades. Choosing either font cascade applies it to the book text and clears the other menu. Each chapter load, reload or history return resets the font to the Constantia cascade; fonts are not restored from saved preferences. Cascades use the first installed font, with edition-specific Chinese fonts retained. Fullscreen keeps reading controls, notes and chapter navigation available; use Exit fullscreen or Escape to return. Browsers without native fullscreen use an expanded reader within the tab.

TEI notes are rendered as numbered, keyboard-accessible popovers in the web reader.

## Project layout

- `src/` contains the Astro site and TEI-to-HTML reader; `src/i18n/` holds the interface catalogues.
- `public/` contains deployable static assets, including committed PDF exports under `public/downloads/`.
- `tei/` contains the curated standalone TEI corpus, schema, validator, and build scripts.
- `corpusdb/` is the prototype SQLite catalogue derived from TEI and the side files (see `corpusdb/README.md`); `docs/corpus-audit/` holds the corpus audit it is based on.
- `assets/` contains local source material used by the TEI preparation pipeline. It is not served or committed; the deployable standalone results live in `tei/`.

See `tei/README.md` for corpus provenance and validation details.
