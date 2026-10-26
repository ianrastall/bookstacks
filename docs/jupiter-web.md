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


## Unified library and independent interface language — 22 October 2026

The language neighborhoods described above are superseded. `/` and all six existing language homepages expose the same complete catalogue. `/authors` preserves the portrait shelf across all 18 authors; each author page groups all editions by work. `/downloads` and its existing localized aliases list every edition with its own TEI/PDF links. Book language is an optional catalogue filter, never an interface-language gate. Existing edition, chapter, download and legacy redirect paths remain valid.

The labeled interface-language selector defaults to browser language preferences, matched in preference order with regional fallbacks and English when no supported interface locale matches. A manual choice is saved locally and can be reset to Automatic. `?ui=fr` (and the other supported locale codes) provides an explicit shareable override and carries through navigation when browser storage is blocked. `?ui=auto` clears an override. Changing interface language keeps the current edition, chapter, filters and reading position; it never substitutes a translation. Simplified Chinese is not automatically selected for an explicit Traditional Chinese preference, and Modern Greek is not treated as Ancient Greek.

Interface text and accessible labels use explicit translation markers; the corpus is never searched and replaced. The document language follows the interface, while literary text, edition titles and contents retain their own language metadata. The reader text retains `translate="no"`; Chinese reading typography follows the edition language even when the controls use another language. Without JavaScript the full catalogue, author lists, editions, contents and downloads remain generated HTML; browser detection and the saved interface override require JavaScript. Localized catalogue links remain available as a no-script fallback.

This follows W3C guidance on [browser language preferences](https://www.w3.org/International/questions/qa-lang-priorities) and [HTML language declarations](https://www.w3.org/International/questions/qa-html-language-declarations). It remains a static GitHub Pages site, at that time using the six existing interface translations (expanded below); no paid service, server runtime or automatic literary translation is added.

## Interface locales for major languages — 23 October 2026

Interface localization now covers 40 locales instead of the six edition languages. Edition languages (`EDITION_LANGUAGES`) and interface locales (`INTERFACE_LOCALES`) are separate types in `src/lib/i18n.ts`; reading routes, catalogue filters and download addresses use only edition languages, so adding an interface locale cannot create, filter or substitute an edition. Existing URLs are unchanged. New static catalogue pages at `/<locale>` provide the no-script fallback for each interface locale, with `hreflang` alternates; `/<edition-language>/downloads` remains limited to the existing six addresses.

Interface messages moved from positional arrays (`c.N`, `j.N`) and per-locale functions to named keys in one catalogue per locale under `src/i18n/locales/`. Unused messages (palette names, theme toggles, a support appeal and unused summaries) were removed. Catalogues are type-checked against English and unit-tested for complete keys, non-empty text, plural forms and placeholders. Counts use `Intl.PluralRules` and `Intl.NumberFormat`; Ancient Greek borrows Modern Greek plural rules because CLDR has none. The browser bundles English and loads the active catalogue on demand.

Browser preferences are matched with `Intl.Locale`: Chinese is chosen by script (zh-TW and zh-HK resolve to Traditional), Portuguese by region (Brazil or Portugal), Norwegian and Nynorsk to Bokmål, and deprecated tags such as `iw` are canonicalized. Modern Greek (`el`) and Ancient Greek (`grc`) are distinct; the previous settings-dialog strings labeled Ancient Greek were Modern Greek and now belong to `el`, with new Ancient Greek strings for `grc`.

Arabic, Hebrew, Persian and Urdu set the document direction to right-to-left. Interface CSS uses logical properties, and direction-bearing arrows mirror. Every element carrying edition text declares the edition's own `lang` and `dir`, so editions remain left-to-right inside right-to-left interfaces. Japanese, Korean and Traditional Chinese interfaces receive matching system font stacks.

Other corrections in this pass: the README described the committed `public/downloads/` PDF exports as ignored preview files (481 files are tracked and served; the documented resolution order now matches `src/lib/library.ts`) and still described language neighborhoods; registry entries and "Other editions" links now carry edition language metadata and name each edition's language; the root language-alias script discovers localized homepages instead of using a hard-coded list; the site now has a favicon. The 34 new translations were drafted without native-speaker review.

Checks: `npm test`, `npm run audit`, `npm run build`, `node scripts/stage_language_root_aliases.mjs`, `npm run test:browser`.

## Reader controls and catalogue preferences — 24 October 2026

Fixed the Jupiter default sans-serif cascade overriding explicit reader selections.
Width controls now extend to 100 rem and remain effective at intermediate desktop
sizes. Fullscreen includes the text, controls, notes and chapter navigation; native
fullscreen is used where available, with an expanded in-tab fallback and Escape
exit. Background controls are inert while expanded.

The catalogue offers 16, 32, 64 or all editions per page. A saved page size can be
overridden with `size=16|32|64|all`; changing filters or size resets pagination.
The initial book-language filter follows browser preferences independently of the
interface locale. Explicit `language=all` restores the unified catalogue, and
changing interface language never changes the current filter or reading route.
This follows Ian’s latest request and supersedes the earlier all-languages default.

Added the complete James Legge English Tao Te Ching as a separate TEI edition.
The other two requested translations need complete sources with clear reuse rights;
see [the source record](chinese-english-sources.md). Site builds remain separate
from source acquisition, TEI import and PDF generation.


### Font control correction — 24 October 2026

The earlier sans-serif fix affected interface typography and reader headings,
but book paragraphs still used the serif stack. Either cascade menu now selects
the book text family; the inactive menu is cleared so only one font choice appears
active. Chinese editions use the corresponding Chinese serif or sans-serif stack,
independent of interface locale.

Ian requested a fresh Constantia default each time. Stored serif/sans-serif values
are no longer read or written, and chapter loads, reloads and history returns reset
both the selected menu values and the text to the default serif cascade. Width,
size and general appearance preferences retain their existing behavior.


### Structural heading title case — 24 October 2026

Chapter, part, volume, book, act, scene and other division titles now use title
case in the contents, reader page titles, hierarchy context and nested headings.
English minor words use the existing PDF exporter's word list. Roman numerals,
initialisms, accents and internal capitals in mixed-case names are retained.
Casing uses the edition language, independently of interface choices; Chinese
characters are unchanged. The hierarchy context no longer forces uppercase.

Formatting applies only to text nodes in the transient display DOM, retaining
inline emphasis, links, IDs and note content. Canonical TEI files, route segments
and PDF publication files are unchanged. PDF generation remains a separate pipeline.


### Font state within a reading session — 24 October 2026

Ian clarified that the chosen font should survive chapter changes during a reading
session. The active family and cascade now use `sessionStorage` under
`bookstacks-reader-font`. A fresh tab session defaults to Constantia; the old
permanent font preferences are still ignored. No font cookie is created.

The head script validates and applies the saved choice before the reader paints.
Reader initialization and `pageshow` restore the same choice into both the CSS
state and dropdowns, including after Back/Forward navigation to an older page.
Only the active font menu has a selected cascade. Missing, invalid or blocked
session storage falls back safely; controls continue to work for the current page.
This supersedes the per-chapter font reset described in the earlier correction.

## Embedded PDF reading, 26 October 2026

Edition pages with same-origin PDFs now offer an embedded, self-hosted PDF.js
reader. The standalone *A Study in Scarlet* supplies both `-light.pdf` and
`-dark.pdf`, generated by the explicitly invoked exporter with `--theme both`.
Existing unsuffixed files and URLs remain valid. The site continues to provide
Light and Dark under Settings > Appearance > Theme. PDF selection initially
follows that setting and supports an explicit separate choice; switching files
preserves the physical page. The PDF.js controls follow the interface locale,
while the text layer retains the book language. PDF reading positions are keyed
by file revision and remain separate from HTML chapter positions. Site builds
and deployment still do not regenerate PDFs or canonical TEI. See
[the export and reader record](pdf-reading-prototype.md) for commands and scope.

The full rollout supersedes the initial separate PDF preference: the embedded
PDF now uses the site's Light/Dark setting, and its theme control updates the
site setting. Read online and Read PDF are explicit, translated options in the
catalogue, author pages, book pages and chapter reader. Every canonical edition
has a pair in the separate `ianrastall/bookstacks-pdf` publication repository.
Its Pages host serves the PDF bytes; PDF.js stays embedded on Bookstacks. The
main repository commits a source-checksummed manifest snapshot, rather than
copying the enlarged publication set into the site's Pages artifact.

The reading layout was subsequently corrected to use the same content column
for HTML and PDF. `view=pdf` selects PDF rendering on the existing chapter route;
the mode buttons replace the rendered surface in place while preserving site
navigation, sidebar, HTML chapter content and the saved PDF page. PDF.js now
renders the page directly with a selectable text layer, page/contents/search
controls and normal site scrolling. The separate iframe reader is no longer
used. Legacy edition-page PDF anchors forward to the appropriate reader route.
