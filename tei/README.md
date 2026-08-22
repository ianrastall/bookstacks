# Bookstacks TEI

The files in the author directories are generated standalone TEI P5 documents.
Rebuild them from the source corpus with:

```powershell
./build_tei.ps1
```

Validate the schema and Bookstacks invariants with:

```powershell
python ./validate_tei.py
```

## Encoding conventions

- One generated file represents one complete work and language. Multi-volume
  source editions such as *War and Peace* and *Anna Karenina* are combined into
  a single work file while retaining numbered internal volume and part levels.
- A translation is always a separate language-specific TEI file. It retains
  its own source hierarchy and is not forced into one-to-one alignment with the
  original-language edition.
- Structural hierarchy follows the source: text, then book/volume/part,
  chapter, and section where those levels exist.
- Every generated division, paragraph without a source ID, `said` element,
  and spoken or attributed `q` element receives a stable `xml:id` at its own
  granularity.
- Stephanus milestones identify their page or section. Bekker line identifiers
  include the current Bekker page, so recurring line numbers remain unique.
- Prose dialogue is encoded with `said`, not dramatic `sp`. Each encoded
  `said` or attributed `q` uses local `who` and `toWhom` pointers to a
  declared `person` or `personGrp`. Participant registers in source
  `standOff` elements are retained rather than flattened into name-only
  header records.
- Dialogue in prose EPUB sources remains prose unless the source provides an
  explicit speaker attribution; the build does not invent literary
  attributions. The Dickens XHTML uses typographic quotation marks but does
  not identify speakers semantically, so no `said/@who` values are fabricated.
- The six Jane Austen novels are generated from `assets/tei/aus.001.xml`
  through `aus.006.xml`. Their chapter hierarchy, participant lists, and
  encoded prose-speaker attributions are retained and normalized.
- `assets/tei/hta.*` contains works by Henry Thomas Austen, not Jane Austen,
  and is intentionally excluded from the generated corpus.
- The Maude *War and Peace* and Garnett *Anna Karenina* translations are
  generated independently from Project Gutenberg EPUBs 2600 and 1399.
  Gutenberg header, contents, and license boilerplate are omitted. Each
  translation retains its own book/part and chapter hierarchy, paragraphs,
  translator notes, poetry, and inline emphasis where present.
- The Dickens editions are independently generated from Project Gutenberg
  EPUBs 98 (*A Tale of Two Cities*), 1023 (*Bleak House*), 766 (*David
  Copperfield*), 967 (*Nicholas Nickleby*), 730 (*Oliver Twist*), 917
  (*Barnaby Rudge*), 968 (*Martin Chuzzlewit*), and 24022 (*A Christmas
  Carol*). Book divisions, numbered chapters or staves and their titles,
  authorial prefaces and postscripts, character lists, paragraphs, letters,
  poetry, contributor credits, and inline emphasis are retained where
  present; Gutenberg header, contents, transcriber notes, and license
  boilerplate are omitted.
- The seven Russian Dostoevsky works are generated from the Digital
  Dostoevsky TEI corpus in `assets/dostoevsky-tei/texts`. Its part, chapter,
  and section hierarchy; front matter; full stand-off character and group
  authorities; and explicit speaker/addressee annotations are retained.
  Multi-party pointer lists are normalized as local TEI references, while
  passages for which the source does not identify a speaker remain
  unattributed. The separately encoded censored chapter *У Тихона* is
  included in the *Бесы* file as a suppressed-chapter textual supplement,
  rather than emitted as a fragmentary eighth work.
- Source-specific HTML constructs are converted to TEI equivalents, and
  divisions that mix blocks with subdivisions are grouped into ordered
  section divisions.

The validator enforces Relax NG validity, unique XML IDs, granular utterance
IDs, qualified ID attributes, and resolvable speaker and addressee pointers
for both `said` and attributed `q` elements.
