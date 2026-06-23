# Bookstacks Translation & Encoding Style Guide

This is the single source of truth for producing **parallel-text** chapters (an
original-language text facing one or more translations). It was written for
*War and Peace* (`2600-full.xml`) but applies to any multi-version book.

Read this before translating or encoding any chapter, and keep choices
consistent with **Chapter I of `2600-full.xml`, which is the reference chapter** —
when in doubt, open it and copy its patterns.

---

## 1. Philosophy

- The translations are **AI-made and that is the point** — there is no dependency
  on a published (Maude/Garnett) translation. Do **not** paste in an existing
  translation.
- Aim for faithful, readable literary English that stays **transparent to the
  source sentence** (good for language learners) without going wooden.
- The **facing original is the quality net**: every translated paragraph sits one
  toggle away from its source, so nothing is unverifiable. Translate honestly;
  do not smooth over or embellish.

## 2. The two-version chapter model

Each chapter holds one `<head>` followed by one or more
`<div type="version">` blocks. The reader renders a toggle that **fully switches**
between versions (no columns). With only one version, no toggle appears.

```xml
<div type="chapter" n="1">
  <head>Volume I, Part One, Chapter I</head>
  <div type="version" xml:lang="en" subtype="translation"> … </div>
  <div type="version" xml:lang="ru" subtype="original"> … </div>
</div>
```

- **Order doesn't set the default** — the page defaults to the version with
  `subtype="translation"` or `xml:lang="en"`; otherwise the first. So a chapter
  that has only the Russian original simply shows Russian (no toggle) until an
  English version is added.
- **Alignment:** translate **one source paragraph → one target paragraph**. This
  1-to-1 rule is what keeps the versions aligned for free. Do not merge or split
  paragraphs across versions.

## 3. Names and the registry (authority)

The `<listPerson>` / `<listPlace>` registries in the `teiHeader` are the **single
authority** for how every name is spelled, including stress accents
(Pávlovna, Vasíli, Bezúkhov, Kutúzov, Hélène, Anatole…). 

- Use the exact registry form everywhere in the translation.
- When a new character/place first appears, **add it to the registry first**
  (with an `xml:id`, name, and a short `<note>`), then use it.
- The registry is shown to readers on the book's contents page.

## 4. Dialogue

Use **em-dash Continental style**, mirroring the Russian original — an em-dash
opens a line of speech; attributions follow after an em-dash:

```
— What would you have me do? — he said at last. — You know, I did all a father can…
```

Do **not** wrap dialogue in English quotation marks. (The parser only adds
quotation marks to `<said>` whose text doesn't already begin with a dash or
quote, so plain em-dash paragraphs render as-is.) Plain `<p>` is fine; `<said>`
is optional and currently not used in the W&P version panels.

## 5. French in the original (this is the special case)

Tolstoy wrote much of the salon speech in **French**, with his own Russian
footnotes translating it. Handle it like this:

**Original (`xml:lang="ru"`) panel** — keep the French exactly as Tolstoy wrote
it, wrapped in `<foreign>`, immediately followed by Tolstoy's Russian gloss in a
`<note>` (which renders as an inline `[bracket]`):

```xml
<foreign xml:lang="fr">— Eh bien, mon prince…</foreign><note>Ну, князь…</note> Ну, здравствуйте…
```

**Translation (`xml:lang="en"` and `xml:lang="es"`) panels** — leave the French text in French, but wrap that span in `<foreign xml:lang="fr">` and add the translation in the `n` attribute:

```xml
— <foreign xml:lang="fr" n="Well, Prince, so Genoa and Lucca…">Eh bien, mon prince…</foreign> Well, good evening…
```

Rendering: `<foreign xml:lang="fr">` shows as a faint **dotted underline** with a `cursor: help` and a tooltip. If there is no `n` attribute (like in the original panel), the tooltip names the language ("French"). If there is an `n` attribute, it adds the translation ("French: [Well, Prince, so Genoa and Lucca…]").

- The `xml:lang` on `<foreign>` tells the parser which language name to use.
- The `n` attribute holds the translated string for the tooltip.
- Footnotes (`<note>`) appear **only in the original panel** — the translation tabs provide the gloss inside the tooltip.
- Names that merely happen to be in Latin script (Pierre, Annette, Buonaparte)
  are **not** French passages — do not flag them.

## 6. Footnotes generally

Tolstoy's footnotes are inlined as `<note>…</note>` → `[bracketed gloss]` placed
**right after the word/phrase they refer to** (not collected at the chapter
bottom). The bracket contains the translation/gloss only.

## 7. Chapter numbering and heads

- `n` on `<div type="chapter">` is the **global, unique** chapter order for the
  whole book. *War and Peace* restarts chapter numbers each Part, so **do not**
  reuse them — number sequentially across the entire novel (1, 2, 3 …).
- Put the human structure in `<head>`: `Volume I, Part One, Chapter I`.

## 8. Orthography

- Normalize the source's archaic stress mark `чтò` → `что`. Keep `ё`.
- Preserve the source's punctuation and paragraphing otherwise.
- Use `<emph>` for author emphasis (the source's italics, e.g. *грипп*),
  `<title>` for work titles (renders as `<cite>`).

## 9. TEI element cheat-sheet (what the parser understands)

| Element | Renders as |
|---|---|
| `<p>` | paragraph |
| `<emph>` | `<em>` |
| `<title>` | `<cite>` |
| `<foreign xml:lang="fr">` | dotted-underlined italic + language tooltip |
| `<foreign xml:lang="fr" n="Trans">` | dotted-underlined italic + "French: [Trans]" tooltip |
| `<note>` | inline `[bracketed]` gloss (muted italic) |
| `<said who="#id">` | speech; adds quotes only if text has no leading dash/quote |
| `<persName ref="#id">` / `<placeName>` / `<rs>` | registry tooltip (dotted) |
| `<pb n="">` | page-break milestone |
| `<lg>` / `<l>` | verse group / line |
| `floatingText`,`opener`,`closer`,`salute`,`signed`,`dateline` | letter styling |

Unknown elements fall through to their inner content.

## 10. Per-chapter workflow

1. Get the source chapter (for W&P, from the Volume HTML via the converter — see
   AGENTS.md → "Translation pipeline").
2. Ensure the Russian original version is in place (the converter does the bulk;
   then add `<foreign>` wrapping + `<note>` brackets where French occurs).
3. Translate paragraph-for-paragraph into the `xml:lang="en"` version; for originally-French spans, leave them in French but wrap them in `<foreign xml:lang="fr" n="[Translation]">`.
4. Add any new people/places to the registry first.
5. `npm run build` and spot-check the chapter in the reader (toggle both ways).

## 11. Roadmap / future languages

The model already supports **N versions** — the toggle loops over all of them and
the label map knows `fr`, `de`, `it`, `la`, `ru`, `en`. Adding another
translation later is purely additive: drop in another
`<div type="version" xml:lang="es" subtype="translation-es">` and a third tab
appears automatically.

Phasing for *War and Peace*:
1. **Russian original** for the whole novel (Volume I is converted; Volumes
   II–IV + epilogues need their source HTML, then the same converter).
2. **English** translations, chapter by chapter (English is the site default).
3. Optionally a **second translation**. A site-wide default second language is
   under consideration — Spanish is the leading candidate (most widely read).
