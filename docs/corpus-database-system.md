# Bookstacks corpus database: system design and implementation handoff

Date: 23 October 2026

Status: proposed system based on Ian's discussion with Codex. This document records the agreed direction and recommends an implementation path. It does not claim that a database, migration, new publication format, or new validation profile has been implemented.

## 1. Purpose and decisions

Bookstacks is primarily for reading books online in a browser. PDF and ePub are generated reading copies. Search across the corpus is an important secondary function. SQLite is proposed as the internal corpus store, not as a reader-facing book format.

Ian's selected direction is to design the database around the structures and editorial requirements of TEI, store the underlying text and structured data, and generate TEI XML from that data. Storing complete XML documents or HTML paragraphs in database fields is not the intended final model.

The objective is more complete and dependable editions. Important requirements should be represented by schema constraints, validation rules, explicit assessments, and recorded review, rather than depending on an LLM remembering instructions each time it imports or edits a book.

Completeness means complete against a declared Bookstacks encoding profile and the selected source. It does not mean using every feature of TEI or inventing scholarly annotations unsupported by the source. Source fidelity and transparent limitations take priority over impressive-looking metadata.

## 2. Current system and preservation boundary

The following observations are from the working checkout on 23 October 2026. Another agent is actively changing the site; inspect current instructions and code again before implementation.

- Canonical publication TEI currently lives in `tei/<author>/*.xml`.
- `tei/README.md` documents source-specific encoding and acquisition conventions.
- `tei/validate_tei.py` applies `tei/tei_all.rng` and project rules, including IDs and participant references. Retain these checks as a baseline, not a claim of full editorial coverage.
- `src/lib/library.ts` currently loads TEI and builds edition metadata, reading units, contents, participant registers, and HTML.
- `tei/build_tei.ps1` and the individual importers prepare the corpus. The current website build does not regenerate it.
- PDF production is separate from site deployment. Existing matching PDF files and release assets must continue working. ePub is a requested output in the proposed system, not an assertion about an existing exporter.

Read `../AGENTS.md`, this repository's `AGENTS.md`, and `../_standards/` before work. Preserve edition identities, source language metadata, existing IDs, reading URLs, source credits, notes, approved portraits, and the unified multilingual catalogue. Interface language remains independent of edition language and must not switch the selected text or chapter.

The present preservation instructions remain in force during research and prototyping. A future authority change must be documented explicitly in the project instructions and pipeline documentation as part of a validated migration. Do not silently reinterpret existing canonical XML as disposable output.

## 3. Proposed authority and publication model

After a successful, explicit cutover:

```text
Retained source material + provenance
                  |
          import into staging
                  |
       structured SQLite corpus
       (drafts and reviewed revisions)
                  |
       validation and review gates
                  |
       immutable edition release
                  |
        deterministic TEI export
                  |
      +-----------+------------+
      |           |            |
 browser HTML    PDF          ePub

Released content also supplies derived plain text and search indexes.
```

The database would become the editorial authority; exported TEI would remain the complete, interoperable representation of a released edition. TEI validation remains a publication gate. Raw source files remain evidence, not a second live editorial authority. HTML, plain text, search indexes, and generated publications are derived artifacts with recorded revision identities.

Keep two operations separate:

1. **Corpus/publication release:** explicitly import or edit, validate, review, freeze a revision, export TEI, and independently generate requested PDF/ePub artifacts.
2. **Website deployment:** consume an already released corpus/TEI and existing publication assets, generate the static website and its indexes, and deploy. It must not acquire sources, revise editions, rebuild the corpus, or generate PDFs/ePubs.

The first implementation should keep the current TEI-to-site boundary. Feeding the reader directly from SQLite can be evaluated later and is not required to establish database authority. Retain Astro/TypeScript and static hosting; no persistent web database server or paid service is required by this proposal.

## 4. Modeling approach

Use explicit relational records for editorial concepts, with ordered content nodes for text that requires nesting. Do not create a separate table for every possible TEI element. Do not use an unrestricted XML-shaped node table as a substitute for domain constraints.

The following are conceptual entities, not final SQL table definitions:

| Entity | Responsibility |
| --- | --- |
| Work | Stable intellectual-work identity and catalogue grouping. |
| Edition | Independent text/translation identity, language, existing identifiers and route mappings. Several editions may share a language. |
| Edition revision | Specific content state, profile version, parent revision, status, and revision provenance. |
| Contributor and contribution | Authors, translators, editors, and other credited roles; support multiple and uncertain/traditional attributions. |
| Source and source use | Bibliographic description, source files/URLs, fingerprints or revision IDs, and the edition sections to which each source applies. |
| Section/content node | Ordered document structure, including front/body/back matter, nested divisions, paragraphs, verse, speeches, and inline content. |
| Participant/register entry | People, groups, places, and other source-supported registers and their identifiers. |
| Reference | Typed, ordered links from content to notes, participants, sources, milestones, or external resources. |
| Asset | Figures and related files, descriptions, credits, fingerprints, and relationships to content. Preserve approved portrait records. |
| Profile and rule | Versioned supported structures, applicability criteria, validation rules, and publication requirements. |
| Feature assessment | What was found, checked, preserved, excluded, or left unresolved in an edition or section. |
| Editorial change and review | What changed, who/what made it, supporting evidence, and review against an exact revision. |
| Release and artifact | Frozen revision, validator/exporter versions, hashes, and produced TEI/PDF/ePub assets. |

Avoid duplicate authority: if sections and paragraphs are typed content nodes, section/paragraph views or detail tables must refer to those nodes, not maintain a separate editable copy of the hierarchy. Store controlled attributes in typed fields or validated detail tables where they carry editorial meaning. Any extension mechanism must have declared names, allowed values, validation, and export mappings; unrestricted JSON must not bypass the profile.

## 5. Text, order, and mixed content

Preserve exact Unicode text, punctuation, meaningful whitespace, and ordering. A paragraph cannot be modeled only as plain text plus a formatting label: it can contain quotations, emphasis, language changes, notes, references, and nested structures.

Illustrative representation of `She called it extraordinary.` with one italicized word:

| Node | Parent | Order | Kind | Text or detail |
| --- | --- | --- | --- | --- |
| p001 | chapter-1 | 1 | paragraph | existing XML ID: p001 |
| n002 | p001 | 1 | text | `She called it ` (trailing space retained) |
| n003 | p001 | 2 | emphasis | rendition: italic |
| n004 | n003 | 1 | text | `extraordinary` |
| n005 | p001 | 3 | text | `.` |

The generated TEI is:

```xml
<p xml:id="p001">She called it <hi rend="italic">extraordinary</hi>.</p>
```

Node IDs above are illustrative. Internal database IDs and public XML IDs are separate concerns. Text fragments need not acquire public XML IDs simply because they have database rows.

The model must also preserve containers and empty milestones: page/line breaks, figures, tables, lists, epigraphs, letters, verse groups/lines, dramatic speeches and stage directions, prose `said`/`q`, editorial alternatives, and stand-off references where present in the actual corpus. Record namespace identities and attributes necessary for faithful export, including `xml:lang`, `xml:space`, rendition and reference semantics. Inherited language must remain distinguishable from an explicitly declared language.

Do not silently strip unsupported elements or flatten them into plain text. Stop promotion of that import, report the exact source location, and extend the profile/model before accepting it. Retain the original source while the issue is unresolved. Import preservation must not be limited to what the current web renderer happens to display.

## 6. Identity and references

- Preserve all existing public `xml:id` values and reader routes. Do not regenerate IDs from paragraph position or text hashes after routine edits.
- IDs are unique within an exported edition document; the same source ID can legitimately occur in another edition. Enforce the appropriate edition/revision scope.
- Keep stable logical identities across revisions while allowing each released revision to reproduce its own content. A database row number alone is not a permanent public identifier.
- Record split, merge, replacement, and deletion mappings when passages change. Define redirects or tombstones for public targets where needed; do not silently reuse an old ID for different content.
- References must preserve their type and ordering, including multi-target attributes. Local pointers must resolve within their intended edition/revision and to an allowed target kind. External URIs follow a separate validation policy.
- Preserve participant groups and stand-off registers. Do not invent speaker/addressee attribution from quotation marks or narrative guesses.
- Translations keep their own hierarchy and reading units. Cross-edition alignment is optional, explicit, evidence-backed data, never an assumption based on matching chapter or paragraph numbers.

## 7. Encoding profile and completeness

Define a versioned **Bookstacks TEI profile** before finalizing SQL. Use a TEI ODD customization if appropriate to maintain a reproducible schema and documentation; choose and document the mechanism during design. Pin the TEI/schema version rather than silently adopting a new upstream release.

The profile must cover the union of structures already preserved in the corpus. New profiles may add requirements, but must not erase richer existing encoding to achieve uniformity. Genre-specific modules can add requirements for drama, verse, correspondence, or other material.

Distinguish three dimensions:

1. **Text and structural fidelity:** the selected source's intended content and organization are preserved.
2. **Editorial and provenance completeness:** edition identity, sources, contributors, transformations, notes, and limitations are accounted for.
3. **Additional scholarly annotation:** named-entity tagging, linguistic annotation, manuscript variants, or similar work is required only when declared by the edition profile. Preserve any such encoding already present.

Do not use a single percentage or “valid TEI” badge to stand for all three. A profile-complete edition may still lack independent scan collation; say so. Existing editions must not be retroactively described as fully reviewed merely because they import or validate.

### Feature assessments

For every applicable feature, record scope (edition or section), assessor, revision, evidence, and assessment date. Keep separate fields for:

| Dimension | Suggested states |
| --- | --- |
| Source presence | unassessed, present, absent, uncertain |
| Treatment | pending, preserved, partially preserved, excluded by declared scope, not applicable |
| Review | unreviewed, automated checks passed, human reviewed, unresolved |

“No notes in source” differs from “notes not checked.” “Source has page numbers, deliberately excluded under this profile” differs from “source has no page numbers.” An exclusion needs a rationale and must not waive a mandatory preservation requirement. Unknown bibliographic facts need an explicit uncertainty record, not fabricated data or placeholder strings that merely satisfy `NOT NULL`.

The initial assessment inventory should include front/back matter, division order, prose, verse, dialogue/stage directions, headings, notes and targets, inline rendition, foreign-language passages, page/line milestones, figures/tables/lists, participant registers, editorial interventions, contributors, source exceptions, and licensing/source-use information. Expand it from a corpus audit rather than treating this list as exhaustive.

## 8. Validation and publication gates

Drafts may be incomplete. Invalid structure must never become a released edition merely because draft data can be stored. Enforce basic integrity continuously, then evaluate completeness and publication requirements against an exact immutable revision.

| Layer | Required checks |
| --- | --- |
| SQLite integrity | Required relationships and values, scoped uniqueness, valid enumerations, and compatible types. Explicitly enable and verify foreign keys on every connection. |
| Structure | Ordered siblings, valid parent/child kinds, no cycles, valid roots, revision/edition containment, required headers and hierarchy. |
| Semantics | Reference target kinds, valid language metadata, contributor roles, note links, preserved registers, profile-specific requirements. |
| TEI export | Well-formed namespaced XML, pinned schema validation, existing Bookstacks rules, and additional profile assertions. |
| Source fidelity | Text/structure comparisons, feature inventories, source fingerprints, and documented transformations/exceptions. |
| Publication review | Required assessments resolved, review evidence current, no blocking issues, reproducible artifact manifest. |

SQLite foreign keys require explicit per-connection configuration; a declared constraint alone is insufficient. Cross-row tree and editorial rules need carefully designed transactions, triggers, and/or validators. Identify the enforcement mechanism and a meaningful failure case for every requirement. [SQLite foreign key documentation](https://sqlite.org/foreignkeys.html)

An LLM may propose imports and corrections, but cannot self-certify a human review. Record automated authorship, tool/model identity where available, and actual review provenance. Content, profile, or relevant exporter changes invalidate dependent approval/check results; stale results must not authorize a new release.

The system cannot prove source fidelity solely from database integrity. Comparison with source evidence remains necessary. Do not claim absence of omissions from schema validity, matching counts, or passing round trips alone.

## 9. Revisions, persistence, and reproducibility

Define the storage lifecycle before making SQLite authoritative:

- Use transactional writes and validated migrations. Prevent readers/exporters from observing half-written revisions.
- Freeze release snapshots; record database schema, profile, importer, validator, and exporter versions and source fingerprints.
- Export deterministically: fixed ordering, explicit encoding, controlled timestamps, stable identifiers, and deterministic serialization rules. Record justified differences from imported XML.
- Choose a source-control strategy that makes text changes reviewable. A binary `.sqlite` file alone is insufficient as a useful review diff. Evaluate deterministic text snapshots/change reports alongside consistent database backups, and document which representation is authoritative and how recovery works.
- Test backup and restoration. Do not copy a live database file casually while writes or a write-ahead log may be active; use a supported consistent snapshot method.
- Preserve original XML snapshots during migration and keep the current release deployable throughout the prototype.
- Record how simultaneous editorial work is coordinated. Do not attempt to merge competing binary database files as if they were text.

No silent two-way synchronization between hand-edited XML and database data. During prototyping XML remains canonical and the database is disposable. After an explicit cutover the database is canonical and XML edits must enter through a documented import/change workflow with conflict checks.

## 10. Search and derived representations

Generate plain text from released structured content, preserving mappings to stable passage IDs and reading URLs. HTML is produced from the same validated edition, not separately maintained text.

Decide how search handles notes, front matter, verse, editorial alternatives, and duplicated text. Results must identify work, edition, language, and location and open the correct reading passage. Distinguish literal edition text from any normalized search representation; never overwrite original text with search normalization.

SQLite FTS5 is a candidate editorial/local search index, not an automatic solution for every language or for static-site delivery. Evaluate tokenization and normalization with actual Chinese, Greek, Russian, and Latin-script examples. Public browser search can use a derived static index; loading the whole corpus database into every visitor's browser is not a requirement. [SQLite FTS5 documentation](https://sqlite.org/fts5.html)

Search indexes, display HTML, and plain-text caches must identify their source release and be regenerable without editorial decisions.

## 11. Implementation sequence for Claude

### Stage 1: audit and profile

Read current instructions and inspect ongoing changes before touching shared files. Inventory TEI elements, attributes, namespaces, nesting patterns, references, source records, and existing validation/export assumptions across the entire corpus. Identify information the reader currently ignores. Produce a machine-readable inventory and a short gap report without rebuilding sources.

Draft the initial profile, feature assessments, preservation matrix, and rule-to-enforcement map. Mark findings as observed, inferred, or unknown. Select representative fixtures from actual content, including English Austen participant attribution, Shakespeare drama/verse, Chinese structure/normalization evidence, notes, nested divisions, and unusual editorial/source structures discovered by the audit.

Deliverables: profile draft/version policy, corpus inventory, proposed relational schema and export mapping, representative fixture list, unresolved decisions. Do not run a corpus-wide migration yet.

### Stage 2: isolated proof

Implement an additive prototype in dedicated new paths, with no changes to production authority or deployment. Choose language/runtime based on existing tools; Python's current TEI pipeline is a practical candidate, not a requirement to replace TypeScript site code.

Import selected existing TEI into a temporary SQLite database, validate its relationships/content, export TEI, and apply the current validator plus profile checks. Include the header, front/back matter, registers, and references, not just body paragraphs. Report unsupported constructs with locations and stop promotion rather than discarding them.

Deliverables: schema migrations, importer, exporter, validators, reproducible commands, meaningful fixtures/tests, and loss/comparison report. Generated prototype databases should not become production sources accidentally.

### Stage 3: prove fidelity and enforcement

Demonstrate semantic TEI round trips: text, whitespace semantics, hierarchy, attributes, namespaces, IDs, links, notes, credits, and registers survive. XML attribute order and indentation outside meaningful text need not be byte-identical; define the comparison precisely. Plain-text equality and XML canonicalization alone are not sufficient acceptance tests.

Show meaningful rejections for missing required source metadata, unresolved references, invalid cross-edition links, illegal structure, cycles, duplicate IDs, unsupported constructs, and stale review results. Show that inserting a passage does not renumber existing IDs. Show that draft incompleteness is recorded while release promotion is blocked.

Render generated TEI through the existing reader and inspect representative complex passages and note interactions. Test PDF/ePub exports separately when introduced. Compare catalogue identities, contents order, public routes, language behavior, and downloads against the baseline.

### Stage 4: migration and authority cutover

Only after the proof passes, inventory all editions for supported import and fidelity. Design backup/restore, reviewable diffs, source retention, release manifests, and rollback. Import the corpus without acquisition or speculative enrichment. Report unresolved exceptions and prevent affected editions from being silently certified.

Document the exact authority change and update applicable instructions and workflows together. Preserve the previous release until replacements pass validation. New completeness gates must not cause accidental withdrawal of existing readable books; define an explicit legacy-release policy while assessments are completed. Do not label legacy content profile-complete without evidence.

### Stage 5: publications and search

Integrate the accepted release exports into the existing static build boundary. Add ePub and corpus search in separate, validated increments. Avoid coupling website deployment to editorial import, source downloads, or publication generation.

## 12. Acceptance criteria

The system is ready for authority cutover only when:

- Every existing edition has a supported mapping or a documented blocking exception; nothing is silently discarded or downgraded.
- Representative complex fixtures and a corpus-wide preservation report establish the defined fidelity guarantees.
- Existing edition/language identities, XML IDs, reader routes, credits, notes, portraits, and publication access remain intact.
- Database constraints and validators demonstrably reject the required failure cases.
- Assessments distinguish absent, unassessed, excluded, partial, and reviewed features; publication claims match evidence.
- A released revision can reproduce validated TEI and be restored from a tested backup without undocumented dependencies.
- A content change yields a useful review diff and cannot inherit stale approval.
- Site deployment consumes a fixed release and cannot mutate the corpus or generate PDF/ePub publications.
- Existing site checks pass for any integration changes; representative browser reading and language behavior are verified.

## 13. Decisions intentionally left open

These need evidence from the audit/prototype, not guesses presented as settled design:

1. Exact SQL schema, node/detail-table boundaries, tree-order representation, and attribute extension mechanism.
2. Precise initial TEI profile and genre modules, schema-generation method, and applicability rules.
3. Database backup, distribution, deterministic text snapshot, version-control, and multi-editor workflow.
4. Revision storage strategy and split/merge identity handling.
5. What source comparison and human review are required for each publication claim, including how legacy releases are represented.
6. PDF/ePub toolchain and validation, source-release manifests, and multilingual search delivery.

Resolve routine implementation choices with the project conventions and evidence. Escalate genuinely editorial choices that alter preservation scope or publication claims with a concrete example and recommendation.

## 14. Suggested first instruction to Claude

> Read `docs/corpus-database-system.md` and the current project/workspace instructions. Begin Stage 1: audit the existing TEI corpus and publication boundaries, define a versioned completeness profile, and propose a database schema with explicit preservation and enforcement mappings. Then build an isolated round-trip proof using representative existing editions. Preserve ongoing work and keep current XML canonical until a validated, documented cutover. Do not rebuild the corpus, regenerate publications, change reader URLs, or deploy as part of the initial proof. Report observed gaps and unsupported structures explicitly; do not flatten or invent content to make the schema pass.
