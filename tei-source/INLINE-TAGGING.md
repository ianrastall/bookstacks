# Inline Tagging Spec (persName / placeName / rs)

**Audience: an automated agent (e.g. Codex).** This is a strict procedure, not a
tutorial. Follow the rules literally. When a rule says NEVER or ALWAYS, it is
absolute. When you are unsure whether to tag, the default is **leave the text
plain** — an untagged name is harmless; a wrong or dangling tag is a defect.

This document covers **inline reference tagging only**: marking names of people,
places, and the referring expressions that stand in for them. It does **not**
cover structural encoding (chapters, verse, dialogue, foreign text, translation
versions) — that lives in [`AGENTS.md`](../AGENTS.md) and
[`TRANSLATION-STYLE.md`](TRANSLATION-STYLE.md).

---

## 0. The one-paragraph summary

Every text has a **registry** in its `<teiHeader>`: a `<listPerson>` of people and
a `<listPlace>` of places, each entry carrying an `xml:id`. In the body, you wrap
mentions of those entities in `<persName ref="#id">`, `<placeName ref="#id">`, or
`<rs ref="#id">`, where `#id` points at a registry entry. The site renders each
wrapped mention as a hover tooltip showing that entry's name and note. **An inline
tag whose `ref` does not resolve to a registry entry is a defect** (a "dangling
ref"): it renders with no tooltip. Your job is to add correct, resolving tags and
to never introduce dangling ones.

---

## 1. The three inline tags

| Tag | Use for | Example |
|---|---|---|
| `<persName ref="#id">` | A literal name or title-of-a-person mention | `<persName ref="#mr-bennet">Mr. Bennet</persName>` |
| `<placeName ref="#id">` | A literal place name | `<placeName ref="#netherfield">Netherfield Park</placeName>` |
| `<rs ref="#id">` | A *referring expression*: an epithet, role, or definite description that stands in for a registered entity but is not its name | `<rs ref="#mrs-bennet">his lady</rs>` |

All three are rendered identically by the parser (`src/utils/teiParser.ts`): a
`<span class="tei-rs">` with a tooltip of `name: note` pulled from the registry.
The tag choice is **semantic**, for correctness and future use — pick the right one
even though the visual result is the same.

`persName` vs `rs` rule of thumb:
- It is (part of) the entity's **actual name or naming title** → `persName`.
  ("Mr. Bennet", "Elizabeth", "Lizzy", "Prince Andrei", "Bolkonsky".)
- It is a **description** that refers to the entity without naming it → `rs`.
  ("his lady", "the count", "the old man", "her sister", "the hostess".)

`placeName` has no `rs` counterpart in practice — a descriptive reference to a place
("the capital") is left plain unless it is clearly standing in as a name.

---

## 2. The registry contract

The registry is the single source of truth. Inline tags are pointers into it.

```xml
<particDesc>
  <listPerson>
    <person xml:id="elizabeth" sex="F">
      <persName>Elizabeth Bennet</persName>
      <persName type="hypocorism">Lizzy</persName>   <!-- optional name variants -->
      <note>The second Bennet daughter; the protagonist.</note>
    </person>
  </listPerson>
</particDesc>
...
<settingDesc>
  <listPlace>
    <place xml:id="netherfield">
      <placeName>Netherfield Park</placeName>
      <note>The estate Bingley leases, near Longbourn.</note>
    </place>
  </listPlace>
</settingDesc>
```

Rules:
1. **Every body `ref` MUST resolve** to a `xml:id` defined in the same file's
   registry. No exceptions. (See §6 for the validation check.)
2. A `<person>` needs `xml:id`, one primary `<persName>`, and a short `<note>`.
   `sex` (`M`/`F`/`U`) is conventional; include it. A `<place>` needs `xml:id`,
   one `<placeName>`, and a `<note>`.
3. The `<note>` is what readers see in the tooltip — make it a one-line, spoiler-
   light identification ("The eldest Bennet daughter."), not a plot summary.
4. Extra `<persName type="...">` children (e.g. `type="hypocorism"` for nicknames)
   document name variants. They do **not** create new ids; all variants belong to
   the one `xml:id`.

### id naming convention
- Lowercase, hyphen-separated, ASCII, derived from the name: `mr-bennet`,
  `anna-pavlovna`, `st-petersburg`.
- Stable forever. Once a body references `#elizabeth`, never rename the id.
- **One entity = one id.** If you find duplicate registry entries for the same
  entity, pick the **canonical** one (the id with the most existing body
  references) and route everything to it; do not invent a third. (Real example
  from War and Peace: Napoleon is `#bonaparte`, NOT the near-duplicate
  `#napoleon_bonaparte`.)

---

## 2a. Phase 0 — build the registry first (the common case)

**Most books in this corpus have NO registry yet** (empty `particDesc` /
`settingDesc`, zero inline tags). For those, the registry does not pre-exist — you
build it. Tagging is then a two-phase job per file:

- **Phase 0 — populate the registry.** Read the text (or the portion in scope) and
  add `<person>` / `<place>` entries for the people and places you will tag, per
  the §2 contract and the inclusion threshold in §5. The registry is the *input*
  to tagging, not an afterthought.
- **Phase 1 — tag the body** against that registry, per §3.

Only when a registry already exists and you are explicitly told not to extend it
does "leave plain because there's no entry" (§3 step 1) mean *stop* rather than
*add an entry*. When building is in scope, a missing-but-certain entity means
**add the entry, then tag** — never tag to an id you have not defined.

---

## 3. Decision procedure (run this for every candidate mention)

For each name or referring expression you encounter in the body:

```
1. Is there a registry entry whose identity this mention CERTAINLY matches?
     NO  → leave it PLAIN. (Do not invent a tag. Optionally flag it — see §5.)
     YES → continue.
2. Is the mention the entity's name/naming-title, or a description?
     name/title   → <persName ref="#id"> (people) / <placeName ref="#id"> (places)
     description  → <rs ref="#id">
3. Wrap the MINIMAL span that carries the reference (see §4).
4. Confirm the chosen #id exists in THIS FILE'S registry (§2 rule 1).
```

The gate at step 1 is the whole game: **certainty + a registry entry.** If either
is missing, do not tag.

---

## 4. What to wrap — span boundaries

- Wrap the **referring words only**, not surrounding punctuation or articles that
  aren't part of the reference.
  - `the <rs ref="#ilya_rostov">count</rs>` — "the" stays outside.
  - `<persName ref="#mr-bennet">Mr. Bennet</persName>` — title is part of the name, stays inside.
- **Do not nest** a reference tag inside another reference tag.
- Wrap each mention separately; do not span across two distinct mentions or across
  a sentence boundary.
- Tag **every qualifying mention** in the text, including repeats — not just the
  first occurrence. (The tooltip should work everywhere the entity appears.)

---

## 5. The hard rules — what to tag and what to leave plain

These encode conventions proven out on the War and Peace corpus. They override
intuition.

**TAG:**
- Proper names of registered people and places, every occurrence — **including
  generic, comparative, or plural-of-name uses** of the name itself ("every body
  said *Mr. Weston* would never marry", "the difference between a *Mrs. Weston* and
  a *Miss Taylor*"). It is still the registered person's name → `persName`.
- Name variants of a registered person (nicknames, surname-alone, patronymic
  forms) → `persName ref` to the same id. ("Bolkonsky", "Prince Andrei", and
  "Andrei" all → `#andrew`.)
- **Identifying definite descriptions** — a kinship term, title, or office that
  picks out exactly one registered character in context → `rs`. ("the count" →
  `#ilya_rostov`; "the countess" → `#helene` in a scene where she's the referent;
  "his lady" → `#mrs-bennet`; "her father" → `#mr-woodhouse`; "his daughter" →
  `#hannah`.)
- **Family-plurals** ("the Rostovs", "the Woodhouses") → `rs` to the **head-of-
  family** id (`#ilya_rostov`, `#mr-woodhouse`). If the book has no single head id
  for that family, leave plain.

**LEAVE PLAIN (do NOT tag):**
- **Pronouns** (he, she, they, it, who). Never tag pronouns.
- **Vocatives / forms of address** ("papa", "mamma", "my dear", "sir", "madam",
  "my lord"). These are address, not reference — tagging every "papa" is noise.
- **Evaluative or transient epithets** that don't *identify* on their own ("her
  friend", "this beloved friend", "the poor creature", "a young man of large
  fortune"). Contrast with identifying descriptions (§TAG): "her father" is unique
  → tag; "her friend" could be anyone → plain.
- **Predicative / role-introducing nouns** ("had been supplied by an excellent
  woman *as governess*") — the word names a role, not (yet) a specific referent.
- **Coordinated shared-surname constructions** that can't be cleanly split
  ("Mr. and Miss Woodhouse"): leave the whole phrase plain rather than mangle the
  shared surname.
- Any name/place with **no registry entry**, or whose identity is **uncertain**.
  Leaving it plain is the correct, complete result — do not add a half-guess tag.
  (Example: a footman called "Pyotr" who *might* be the registered servant
  `#petrusha` but the text doesn't confirm it → plain.)
- **Sweeping honorifics / offices** used generically, even for a real person:
  "the sovereign", "государь", "the Tsar", "the Emperor", "His Majesty". These
  stay plain by documented exception — they read as imperial honorifics, not as
  references to a registry character.
- Generic group/role nouns that don't pick out one registered entity ("the
  servants", "the guests", "a soldier").
- Descriptive references to places ("the capital", "home") — `placeName` is for
  actual place names.

**Inclusion threshold — who/what earns a registry entry (and thus tags):**
- **Register** a named entity that is *individuated* and either recurs or has a
  role in events — principals, and named minor characters/places that come back or
  matter (e.g. the coachman "James" and housemaid "Hannah" in *Emma*; the
  housekeeper "Mrs. Hill" in *Pride and Prejudice*; "Randalls", "Brunswick
  Square").
- **Leave plain** incidental, single-mention background names with no ongoing role
  ("Farmer Mitchell", a place named once in passing). Do not register them; do not
  tag them.
- When genuinely unsure whether an entity clears the bar, **leave it plain** — an
  untagged name is complete and correct; a noisy registry of walk-ons is not.

---

## 6. Adding a registry entry

This is normal work, not an exception — it is Phase 0 for any book without a
registry (§2a), and the routine fix whenever a certain, in-scope entity is
missing. (The only time you must *not* add one is when a task explicitly freezes
the registry; then a missing entity means leave-plain.) To add an entry for a
real, certain entity that clears the §5 threshold:

1. Add a `<person>`/`<place>` entry with a fresh, convention-following `xml:id`,
   a `<persName>`/`<placeName>`, and a one-line `<note>`. Place it near related
   entries.
2. If the same entity is referenced in **other** files for the same book (e.g.
   the `_en`, `_es`, `_ru` files of a parallel text), add a matching entry to
   **each** file's registry — registries are per-file and can diverge, so verify
   each one. (Real gotcha: the War and Peace `_es` registry historically lacked
   entries the `_en` registry had.)
3. Then tag the body occurrences.

**Resolving an existing dangling ref:** if body text already contains
`ref="#someid"` with no matching registry entry, the fix is to *define* that id in
the registry (which retroactively resolves every occurrence), not to strip the
tags — unless the id is a stray duplicate, in which case normalize the attribute
to the canonical id (§2).

---

## 7. Worked examples

**Pride and Prejudice (English prose), body:**
```xml
<p>Before <persName ref="#mr-bennet">Mr. Bennet</persName> could make any
reply, <rs ref="#mrs-bennet">his lady</rs> cried out, "A young man of large
fortune has taken <placeName ref="#netherfield">Netherfield Park</placeName>."</p>
```
- "Mr. Bennet" = name → `persName`.
- "his lady" = description of his registered wife → `rs`.
- "Netherfield Park" = place name → `placeName`.
- "A young man of large fortune" is **not** tagged — at this point it's an
  unidentified description (and only becomes `#bingley` once named).

**War and Peace (registered character via name variants):**
```xml
<persName ref="#andrew">Prince Andrei</persName> ... later just
<persName ref="#andrew">Bolkonsky</persName> ... the <rs ref="#andrew">prince</rs>.
```
All three resolve to the one `#andrew` entry.

**Honorific exception (leave plain):**
```xml
<p>... bowing low before the sovereign, who said nothing.</p>
```
"the sovereign" is **not** tagged, by §5.

---

## 8. Validation — required before considering the file done

Run all three:

1. **Well-formed XML.** The file must parse. (e.g. `python -c "import
   xml.etree.ElementTree as ET; ET.parse('<file>')"`.)
2. **No dangling refs.** Every `ref` id in the body must have a matching
   `xml:id` in that file's registry. Note TEI allows space-separated multi-value
   refs (`ref="#a #b"`), so split on whitespace and strip a leading `#` from each
   token before comparing. The following prints any body id missing from the
   registry (must be empty):
   ```bash
   python -c "
   import re,sys
   s=open(sys.argv[1],encoding='utf-8').read()
   body={t.lstrip('#') for m in re.finditer(r'ref=\"([^\"]+)\"',s) for t in m.group(1).split()}
   reg=set(re.findall(r'xml:id=\"([^\"]+)\"',s))
   d=sorted(body-reg); print('DANGLING:',d if d else 'none')
   " tei-source/<file>.xml
   ```
   Any id listed is a defect to fix (define it per §6, or correct the attribute).
3. **Body text unchanged.** Tagging must only *insert* markup — the reader's words
   must stay byte-identical. Strip all tags and compare, but **scope the check to
   `<body>…</body>`**: Phase-0 registry additions legitimately add text in the
   header (names, notes), so a whole-file text compare gives false positives.
   ```bash
   python -c "
   import re,sys
   def body(p):
     s=open(p,encoding='utf-8').read(); b=s[s.index('<body>'):s.index('</body>')]
     return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',b))
   print('BODY TEXT:', 'unchanged' if body(sys.argv[1])==body(sys.argv[2]) else 'CHANGED!')
   " <before>.xml <after>.xml
   ```
4. **Build passes.** From the repo root: `npm run build` (runs `astro check` +
   build). Then spot-check in `npm run dev` that tooltips appear on tagged mentions.

For a parallel-text book, run 1–3 on **each** language file; ids and registries are
per-file.

---

## 9. Invariants (never violate)

- **Text content is never altered by tagging.** Adding/removing inline tags changes
  markup only — the reader's words, punctuation, spelling, quotes, and dashes stay
  byte-identical. Do not normalize anything while tagging.
- Never introduce a dangling `ref`.
- Never tag a pronoun.
- Never tag to an id you have not confirmed exists in that file's registry.
- When uncertain, leave it plain.
