# Bookstacks

Bookstacks is a statically generated reading site for complete books encoded as TEI P5. Each XML file in `tei/` is a standalone work and language edition; related editions are grouped at the work level without assuming chapter-by-chapter alignment.

## Development

```sh
npm install
npm run dev
```

Use `npm run build` for the same type check and static production build used before deployment. The generated site is written to `dist/`.

## Edition downloads

Bookstacks distributes only the canonical TEI source and, when supplied, a PDF. The site build does not generate publication files or fetch them from a release service. Every TEI file under `tei/<author>/` is downloadable from its book page and the downloads index.

To publish a PDF, commit it beside its matching TEI file with the same basename:

```sh
tei/austen/austen_emma_eng.xml
tei/austen/austen_emma_eng.pdf
```

The matching PDF link appears automatically because the file exists in the repository; without that file, the site shows only the TEI download. The optional `scripts/build_exports.py` tool remains available for explicitly invoked local PDF creation, but neither `npm run build` nor the deployment workflow runs it. Its output is ignored until a selected PDF is copied beside its TEI source and committed.

For local review, the Downloads page also detects exporter output at `public/downloads/<author>/<edition>/<edition>.pdf`. These ignored files are preview-only; a production PDF still needs to be copied beside its matching TEI source and committed.

## Language neighborhoods

Canonical routes begin with a site language (`/en/`, `/fr/`, `/grc/`, or `/ru/`). Choosing a flag changes the interface language and filters the library to editions in that language. Entering a book through one of its language-specific routes does the same. Legacy unprefixed reading routes redirect to the corresponding canonical neighborhood.

TEI notes are rendered as numbered, keyboard-accessible popovers in the web reader.

## Project layout

- `src/` contains the Astro site and TEI-to-HTML reader.
- `public/` contains deployable static assets.
- `tei/` contains the curated standalone TEI corpus, schema, validator, and build scripts.
- `assets/` contains local source material used by the TEI preparation pipeline. It is not served or committed; the deployable standalone results live in `tei/`.

See `tei/README.md` for corpus provenance and validation details.
