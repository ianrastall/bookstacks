# Bookstacks Jupiter website

Implemented 22 October 2026 at `D:/jupiter/bookstacks`, using the existing `ianrastall/bookstacks` repository history and `bookstacks.org` GitHub Pages deployment. The clean current source was `D:/dev/proj/bookstacks` at `0eb7b78`. Older checkouts under `D:/GitHub/bookstacks` and `bookstacks-v0` contain separate local work and remain untouched. Their modified portraits, source deletions and unpublished files were not silently merged.

## Library and reader

The root page searches all published language editions by author/title, with language and author filters, pagination and shareable URLs. Every edition and initial reading link is ordinary generated HTML. Each language neighborhood retains its author portraits, author pages and contents; its author index can now filter titles as well as names. The six existing site languages remain English, French, Spanish, Ancient Greek, Russian and Simplified Chinese. Canonical and legacy reading routes, language switching and edition boundaries remain intact; translations are not assumed to have aligned chapter structures.

The shared shell follows Text Utilities and Chess Nerd: Astro, TypeScript, plain CSS semantic tokens, system interface fonts, Lucide shell icons and Settings → Appearance. Warm dark is the first-run default; stored light/dark choices remain. Automatic accent uses the browser's CSS system accent where exposed, with the Jupiter fallback, custom choice and reset. Stored explicit palette choices migrate to custom accents, while portrait backgrounds remain artwork colors. New appearance controls are localized in all six interfaces. Copy is functional and contains no promotional taglines.

Book typography and reading controls remain specialized. The starting reading size is 20 CSS pixels, with a greater enlargement range, width adjustment and font choices. Stored choices persist where available; blocked storage does not prevent reading or note controls. Phone reading controls collapse into a disclosure. Long verse lines retain their line breaks and wrap within narrow columns; phone footnotes use a bounded panel. Semantic TEI rendering and note relationships are unchanged.

## Preserved publication boundaries

The canonical files in `tei/`, source credits, approved portrait files and `src/lib/library.ts` corpus/renderer logic are unchanged. The XML parser dependency is updated to a patched version; unit/browser checks cover the actual corpus and public reading workflows. The library retains 18 published authors, 148 works and 257 language editions.

TEI XML downloads are generated from the canonical XML files through the existing route. PDF links still prefer a matching committed PDF beside its XML, then the matching `publications-*` release asset. Local ignored exporter output remains preview-only. `scripts/index_release_pdfs.mjs` still indexes existing release PDFs before deployment. The site build and CI do not regenerate TEI or run PDF exports. The existing sitemap and language-root aliases remain in the deployment sequence.

Dependencies are pinned; Node 24.13.0, Astro 7.4.2, TypeScript 6.0.3, Vitest and Playwright follow the Jupiter baseline. Deployment audits dependencies, tests the catalogue and corpus addressability, builds a single static artifact, checks reader/library/download workflows in Chromium and deploys that artifact. Firefox/Safari verification is not claimed.

Checks: `npm test`, `npm run audit`, `npm run build`, `node scripts/stage_language_root_aliases.mjs`, `npm run test:browser`. Existing analytics remain. Material Icons used inside retained reader pages are now hosted with the site, so navigation icons do not depend on Google Fonts; no new paid backend or hosting service is introduced.
