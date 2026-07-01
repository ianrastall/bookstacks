# TEI Ingest Checklist

How to take a freshly-added `tei-source/*.xml` book from "sitting in the folder"
to "correctly rendered on the site." Written to be handed to any agent: pick a
book from the table in **Part C**, do its listed tasks, tick them off, rebuild.
Do **not** improvise beyond a book's task list — if something isn't covered,
add it to that book's row rather than silently changing scope.

The site auto-discovers every `tei-source/*.xml`; there is no manifest to edit.
"Integration" therefore means making each file conform to what the parser and
conventions expect. All the parser facts below are load-bearing — read Part A
before touching a file.

---

## Part A — The reusable procedure (how the site actually works)

Run this checklist against every new book. Sources: [`AGENTS.md`](../AGENTS.md),
[`teiParser.ts`](../src/utils/teiParser.ts), and the Henry James / Emma work.

### A1. Author name → slug → portrait (DO THIS FIRST — it can split an author)
- The site author **slug** is `slugifyAuthor(<author display name>)`. That helper
  assumes **"First Last"** input and emits **surname-first** (`Jane Austen` →
  `austen-jane`; `Leo Tolstoy` → `tolstoy-leo`).
- A **"Last, First" comma form breaks it**: `Austen, Jane` → `jane-austen`
  (a DIFFERENT slug → a book filed under a *second, split* author page);
  `Turgenev, Ivan Sergeevich` → `sergeevich-turgenev-ivan` (garbage).
- Patronymics are dropped by convention (`Fyodor Dostoevsky`, not
  `Fyodor Mikhailovich Dostoevsky`), because the portrait files are named
  surname-first with no patronymic (`turgenev-ivan.png`, `dostoevsky-fyodor.png`).
- **Rule:** the `<author><persName>` text must be **"First Last", no comma, no
  patronymic**, so the slug matches the existing `public/img/authors/<slug>.png`
  and any sibling books by the same author. Preserve any
  `<note type="dates">…</note>` inside the persName.
- **Verify:** `slugifyAuthor(name)` equals the portrait filename stem; if a
  portrait exists at `public/img/authors/<slug>.png`, the built author page emits
  `<img … src="/img/authors/<slug>.png">`. If the file prefix
  (`<author-slug>_<title>`) disagrees with the slug, rename the file(s) to match.

### A2. Chapter `@n` must be globally unique per book (or chapters vanish)
- The parser builds chapters from `<div type="chapter">` and keys them in a Map by
  `@n`. **Duplicate `@n` ⇒ later chapters silently overwrite earlier ones** (the
  Emma / Ambassadors bug). A book that restarts numbering per part/volume/book, or
  bundles apparatus numbered `I…` ahead of the novel, will lose chapters.
- **Check:** count `<div type="chapter">` vs unique `@n`. If they differ, find why
  (restart? bundled front matter? a second work? a literal duplicate) and fix so
  every reading unit ends up with a unique `@n` in document (reading) order.

### A3. Nothing readable is silently dropped
- The parser renders **only `<div type="chapter">`** (plus the drama and
  volume-grouped paths). Content in a `<div>` of any other type — or a bare
  `<div>`, or loose `<p>` in `<body>` — is **dropped**.
- Decide per block: **the author's own text** (a Turgenev epilogue, a James
  preface, a framing prologue) → keep, by retyping its `<div>` to
  `type="chapter"` (front matter as `n="0"`, or a real chapter). **Third-party /
  edition apparatus** (translator's or critic's Introduction, "Biographical
  Note", "Criticisms and Interpretations", "List of Characters", publisher title
  pages, Gutenberg TOC/boilerplate) → **strip** per AGENTS.md ("keep the work's
  own reading structure").
- **Check:** for each file, look for body `<p>`/non-chapter `<div>` before the
  first chapter and between chapters; classify each as keep-or-strip.

### A4. One file = one work
- Book identity is `slugify(<title>)`; one file becomes one site book. If a
  Gutenberg volume **bundles two works** (e.g. *The Torrents of Spring* +
  *First Love*), split it into one file per work, or (if the user wants them kept
  together) model them as top-level groups (see A6).

### A5. Heads / titles / registries
- **Title** is English-facing and clean: drop edition subtitles like "A Novel",
  fix casing (`On the eve` → `On the Eve`). Title drives the slug/URL, so settle
  it before sharing links. (Convention: all `<title>` in English.)
- **Chapter heads:** a bare Roman `<head>I</head>` renders as the chapter title
  "I". That's acceptable for a flat single-sequence novel. If the book has
  internal Books/Parts, qualify or nest them (A6).
- **Registries** (`listPerson`/`listPlace`) are optional; absent = no reader
  tooltips. Adding them is the separate inline-tagging track, **not** part of
  ingest.

### A6. Volume / Book / Part hierarchy (only if the book has one)
- Flat novels need nothing here. For a book with real internal divisions, the
  parser supports a generic **Volume → Book → Chapter** nested TOC:
  nest `<div type="volume"> [> <div type="book">] > <div type="chapter">` (leaf);
  front matter as a body-level chapter outside the volumes. Gate: presence of
  `type="volume"` with **no** `type="section"` (the guard that keeps Magic
  Mountain’s chapter→section books on the older 2-level path). See
  `parseVolumeGroupedChapters` / `buildGroupedTocTree` in `teiParser.ts`. Reading
  text must be preserved verbatim through any restructuring.

### A7. Verify
- `npm run build` (runs `astro check` + build) must be **green (0 errors)**; a
  fatal XML error means the file isn't well-formed. Confirm the book's chapter
  page count and that a previously-broken chapter now renders. For structural or
  portrait changes, spot-check the built `dist/` HTML (or `npm run dev`): author
  page shows the portrait; book index lists chapters in order; prev/next works.
- When editing content programmatically, **preserve reading `<p>` text
  byte-for-byte** and assert it (the James scripts diff `<p>` lines / re-extract
  chapters before writing).

---

## Part B — Cross-cutting fix for THIS batch (Austen S&S + 6 Turgenev)

Applies to all 7 new files. **Do this before per-book work.**
- Fix every `<author><persName>` per A1:
  - `Austen, Jane` → `Jane Austen`  (slug `austen-jane` — must match the EXISTING
    Austen books; otherwise S&S splits off a second "jane-austen" author).
  - `Turgenev, Ivan Sergeevich` → `Ivan Turgenev`  (slug `turgenev-ivan`, matches
    `public/img/authors/turgenev-ivan.png`).
- Rename the 6 Turgenev files from the `turgenev-ivan-sergeevich_…` prefix to
  `turgenev-ivan_…` so the file prefix matches the slug (cosmetic but per AGENTS.md).
- Titles (A5): `On the eve: A novel` → `On the Eve`; `Rudin: A Novel` → `Rudin`.
  Leave `Sense and Sensibility`, `A House of Gentlefolk`, `Fathers and Children`,
  `Virgin Soil` as-is.

---

## Part C — Per-book task table (tick and rebuild)

Status: ☐ todo · ◐ in progress · ☑ done. **DECISION** = needs the user's call
before an agent proceeds (see Part D questions).

| Book (file) | State | Tasks |
|---|---|---|
| **Sense and Sensibility** `austen-jane_sense-and-sensibility_en.xml` | ☑ **DONE** — 50 ch under `austen-jane` | ☑ B: `Austen, Jane`→`Jane Austen` (verified: joins existing Austen author, no split). Editorial Introduction / Gutenberg TOC note are non-chapter → dropped. ☑ build. |
| **A House of Gentlefolk** `turgenev-ivan_a-house-of-gentlefolk_en.xml` | ☑ **DONE** — 45 ch | ☑ B: author + file renamed to `turgenev-ivan_…`. ☑ build. |
| **On the Eve** `turgenev-ivan_on-the-eve_en.xml` | ☑ **DONE** — 35 ch | ☑ B: author + rename + title→`On the Eve`. Garnett Introduction + character list dropped. ☑ build. |
| **Virgin Soil** `turgenev-ivan_virgin-soil_en.xml` | ☑ **DONE** — 30 ch | ☑ B: author + rename. Loose translator-credit `<p>` dropped. ☑ build. |
| **Fathers and Children** `turgenev-ivan_fathers-and-children_en.xml` | ☑ **DONE** — 28 ch (novel) | ☑ B. ☑ Stripped apparatus (Biographical Note, Criticisms I–V fake chapters, List of Characters) per decision #1 → clean 28-ch novel, ch 1 = the novel's opening. ☑ build. Script: scratchpad/strip_turgenev.py. |
| **Rudin** `turgenev-ivan_rudin_en.xml` | ☑ **DONE** — 13 units (12 ch + Epilogue) | ☑ B + title→`Rudin`. ☑ Stripped Stepniak Introduction (the mis-tagged first ch-I); ☑ kept Turgenev's Epilogue as trailing chapter n=13 (decision #2). ☑ build. Script: scratchpad/strip_turgenev.py. |
| **Torrents of Spring / First Love** `turgenev-ivan_the-torrents-of-spring_en.xml` | ⛔ **ON HOLD — DO NOT COMMIT** | Currently renders only Torrents (44 ch); First Love collides + is invisible; source missing ch VI, XVII (Torrents) and IX (First Love). Per decision #4, **waiting for corrected/complete source XML**. When it arrives: split into two books `turgenev-ivan_the-torrents-of-spring` + `turgenev-ivan_first-love` (decision #3), renumber each to unique `@n`, build. |

---

## Part D — Decisions (RESOLVED 2026-06-30)

1. **Third-party apparatus** → **STRIP all of it** (Fathers & Children's
   Criticisms/Bio Note/Character list; Rudin/On the Eve/S&S Introductions). Done.
2. **Rudin epilogue** → **KEEP as a chapter**. Done.
3. **Torrents of Spring + First Love** → **SPLIT into two separate books**.
   Pending source (see #4).
4. **Missing chapters** (Torrents VI, XVII; First Love IX) → **WAIT for corrected
   source**. Torrents file is on hold and must not be committed until complete
   XML is supplied; then apply #3.

---

## Part E — Tools / reference
- Verify build: `npm run build`. Quick look: `npm run dev`.
- Parser: [`src/utils/teiParser.ts`](../src/utils/teiParser.ts) — `parseChapters`
  (flat), `parseVolumeGroupedChapters` + `buildGroupedTocTree` (nested),
  `slugifyAuthor`/`slugify`.
- Prior art (patterns + verification style): the Henry James integration —
  line-oriented transforms that keep `<p>` text invariant, renumber globally,
  and re-extract to prove no content lost.
- Conventions: [`AGENTS.md`](../AGENTS.md),
  [`INLINE-TAGGING.md`](INLINE-TAGGING.md) (separate later track),
  [`TRANSLATION-STYLE.md`](TRANSLATION-STYLE.md).
