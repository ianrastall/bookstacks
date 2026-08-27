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
- Six independent Spanish Jane Austen editions are generated from the EPUBs
  in `assets/source-epub`. Their logical chapter boundaries are reconstructed
  independently of EPUB file splits; front and back matter, source title
  pages, two-volume hierarchy, contents tables, print-page milestones,
  explicit display letters, verse, inline typography, source trailers, and
  publisher notes are retained where present. Prose dialogue remains
  unattributed because the EPUB XHTML does not identify speakers.

To rebuild only the English and Spanish Austen editions from the repository
root:

```powershell
./tei/build_tei.ps1 -Author Austen
```

To rebuild just the six Spanish EPUB conversions:

```powershell
python tei/build_spanish_austen_epubs.py --source-dir assets/source-epub --output-dir tei/austen --schema tei/tei_all.rng
```
- George Eliot's *Middlemarch* is generated from the sibling
  `corpus-eliot-middlemarch-tei` repository. Its eight HTML-like source
  fragments are repaired and consolidated into one TEI book containing the
  Prelude, Books I-VIII, Chapters I-LXXXVI, and Finale. Source dialogue,
  represented thought, free indirect discourse, and narratorial person
  annotations are retained with resolvable participant references.
- Shakespeare's 38 normalized standalone files are retained directly in
  `tei/shakespeare`; the deleted root-level legacy inputs are no longer build
  dependencies. Acts and scenes, cast lists, speakers, and typed stage
  directions are retained. Dramatic prose remains paragraph content inside
  `sp`, while verse remains lineated as `sp/lg/l`.
- Thirty-seven French Shakespeare plays are generated from Project Gutenberg
  EPUB XHTML translated by François Guizot. Acts, scenes, speakers, prose
  speeches, stage directions, character lists, songs and verse, editorial
  notices, inline typography, and referenced translator notes are retained.
  Five accompanying poetry volumes—*Venus and Adonis*, *The Rape of Lucrece*,
  *A Lover's Complaint*, the *Sonnets*, and *The Passionate Pilgrim*—are
  explicitly excluded because they are not plays.
- Seven Henry James novels are generated from the root-level
  `james-henry_*_en.xml` files. Their volume, book, chapter, preface, paragraph,
  poetry, inline typography, and source metadata structures are retained.
- Six root-level `turgenev-ivan_*_en.xml` sources generate eight Ivan Turgenev
  works. The Gutenberg omnibus source is separated into *The Torrents of
  Spring*, *First Love*, and *Mumu*; opening frames remain prologues, untyped
  numbered divisions are restored as chapters, and *On the Eve* title,
  translation, introduction, and character-list matter remains accessible.
- Seven matching Russian Turgenev editions are generated from the paginated
  public-domain HTML at the Internet Library of Alexei Komarov. The importer
  caches the source pages in ignored `assets/ilibrary/turgenev`, records each
  stated print source, and retains headings, paragraphs, verse, notes,
  epigraphs, dedications, ornaments, inline emphasis, and source-section
  boundaries. *Virgin Soil* is excluded because the catalog does not contain
  its Russian original, *Новь*.

To refresh or rebuild only these Russian editions from the repository root:

```powershell
python tei/build_ilibrary_turgenev.py --cache-dir assets/ilibrary/turgenev --output-dir tei/turgenev --schema tei/tei_all.rng
```

Existing cached HTML is reused. Pass `--refresh` to download it again, or
`--work <slug>` to rebuild one selected title.
- Six root-level `bronte-*_*_en.xml` sources generate separate Anne, Charlotte,
  and Emily Brontë shelves containing *Agnes Grey*, Charlotte Brontë's four
  supplied novels, and *Wuthering Heights*. Four `chesterton-g-k_*_en.xml`
  sources generate the G. K. Chesterton shelf. Their chapter hierarchies,
  front matter, paragraphs, poetry, figures, inline typography, and source
  metadata are retained.
- `assets/tei/hta.*` contains works by Henry Thomas Austen, not Jane Austen,
  and is intentionally excluded from the generated corpus.
- The Maude *War and Peace* and Garnett *Anna Karenina* translations are
  generated independently from Project Gutenberg EPUBs 2600 and 1399.
  Gutenberg header, contents, and license boilerplate are omitted. Each
  translation retains its own book/part and chapter hierarchy, paragraphs,
  translator notes, poetry, and inline emphasis where present.
- Tolstoy's *Childhood, Boyhood, and Youth* is compiled from three Tolstoy
  Digital Russian TEI works and three independent C. J. Hogarth Project
  Gutenberg translations (ebooks 2142, 2450, and 2637). *The Cossacks* pairs
  the Tolstoy Digital Russian TEI with the Maudes' Project Gutenberg
  translation (ebook 4761).
- The bilingual Tolstoy *Novellas* volume contains *Family Happiness*, “God
  Sees the Truth, But Waits,” *The Death of Ivan Ilyitch*, *The Kreutzer
  Sonata*, *The Devil*, *Father Sergius*, *Master and Man*, *Hadji Murad*, and
  *The Forged Coupon*. Russian works come from Tolstoy Digital. English texts
  are selected from the Standard Ebooks *Short Fiction* and *Hadji Murad*
  repositories; each work remains a separate internal division, with its
  chapters, epigraphs, inline typography, and referenced endnotes retained.
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
- Five independent English Dostoevsky translations are generated from Project
  Gutenberg EPUBs 2554 (*Crime and Punishment*, Constance Garnett), 2638 (*The
  Idiot*, Eva Martin), 28054 (*The Brothers Karamazov*, Constance Garnett), 600
  (*Notes from the Underground*, Constance Garnett), and 8117 (*The Possessed /
  Demons*, Constance Garnett). Their translator or authorial front matter,
  part/book/epilogue hierarchy, chapters, subchapter sections, paragraphs,
  letters, poetry, inline typography, and notes are retained; standalone end
  labels are encoded as trailers, while referenced notes replace their source
  markers inline and unreferenced editorial codas attach to the preceding
  paragraph rather than being flattened at the end of a division.
- Source-specific HTML constructs are converted to TEI equivalents, and
  divisions that mix blocks with subdivisions are grouped into ordered
  section divisions.
- Plato's full 36-work shelf is generated in independent Ancient Greek and
  English TEI editions. *The Republic* uses its dedicated converter to retain
  all ten books and Stephanus divisions, and is included automatically when
  rebuilding Plato or the complete corpus.

The validator enforces Relax NG validity, unique XML IDs, granular prose and
dramatic utterance IDs, qualified ID attributes, preservation of dramatic
verse/prose structures, and resolvable speaker and addressee pointers for both
`said` and attributed `q` elements.
