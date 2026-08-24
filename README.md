# Bookstacks

Bookstacks is a statically generated reading site for complete books encoded as TEI P5. Each XML file in `tei/` is a standalone work and language edition; related editions are grouped at the work level without assuming chapter-by-chapter alignment.

## Development

```sh
npm install
npm run dev
```

Use `npm run build` for the same type check and static production build used before deployment. The generated site is written to `dist/`.

## Publication exports

The TEI editions are canonical. `scripts/build_exports.py` derives a standard cover and these delivery formats for every published edition:

- EPUB 3 and PDF for reading;
- self-contained offline HTML;
- DOCX and Markdown for editing and reuse;
- a LaTeX source bundle, including the OFL-licensed Source Serif font used to compile the PDF;
- JSONL chunks with work, edition, language, hierarchy, annotation, source, and license metadata for search and LLM ingestion.

Install Python 3, Pandoc, and Tectonic, then install the pinned Python packages and run the exporter:

```sh
python -m pip install -r requirements-exports.txt
npm run exports
```

`npm run exports:sample` builds the French edition of *All's Well That Ends Well* as a quick end-to-end check. Local files default to `public/downloads/` and are intentionally ignored by Git.

Website deployment and publication generation are independent. The Pages workflow builds only the static Astro site. A separate publications workflow runs when canonical TEI or export-toolchain inputs change, restores unchanged validated editions from cache, regenerates stale editions, validates every EPUB with W3C EPUBCheck, and publishes changed binaries to stable GitHub Release groups. A publication failure therefore leaves the last valid files online without blocking a website deployment.

Per-edition manifests include checksums and structural validation results; the complete JSONL corpus, manifest, and schema notes are published as their own release group. The site links directly to those durable assets. By default they live in this repository, but they can be moved without changing site code: set the `PUBLICATIONS_REPOSITORY` Actions variable and a `PUBLICATIONS_TOKEN` secret for the publication workflow, then set `PUBLICATIONS_BASE_URL` to the new repository's `https://github.com/OWNER/REPOSITORY/releases/download` URL for the Pages workflow.

## Language neighborhoods

Canonical routes begin with a site language (`/en/`, `/fr/`, `/grc/`, or `/ru/`). Choosing a flag changes the interface language and filters the library to editions in that language. Entering a book through one of its language-specific routes does the same. Legacy unprefixed reading routes redirect to the corresponding canonical neighborhood.

TEI notes are rendered as numbered, keyboard-accessible popovers in the web reader and as true footnotes in DOCX, EPUB, Markdown, and PDF exports.

## Project layout

- `src/` contains the Astro site and TEI-to-HTML reader.
- `public/` contains deployable static assets.
- `tei/` contains the curated standalone TEI corpus, schema, validator, and build scripts.
- `assets/` contains local source material used by the TEI preparation pipeline. It is not served or committed; the deployable standalone results live in `tei/`.

See `tei/README.md` for corpus provenance and validation details.
