# Corpus database prototype

Stage 2 of [the corpus database plan](../docs/corpus-database-system.md), following [the Stage 1 audit](../docs/corpus-audit/README.md). Ian chose the hybrid boundary on 23 October 2026: **TEI XML stays the authority for literary text; SQLite holds catalogue, provenance, assessment, validation and release records**, each pointing into TEI by edition, file hash and `xml:id`.

This is an additive prototype. The current authorities are unchanged: TEI in `tei/`, `src/data/author-profiles.json`, `WORK_TITLES` and `LANGUAGE_DATA` in `src/lib/library.ts`, the source registers in `tei/`, and the PDF manifests. The database is derived from them, written to ignored `tmp/corpusdb/`, and can be deleted and rebuilt at any time. Nothing here reads from or writes to the site build, deployment, TEI files or PDFs.

## Commands

Python 3.14 with `lxml` (`corpusdb/requirements.txt`; on this machine use `py`, not the 3.12 `python` first on Git Bash's `PATH`).

```sh
py -m corpusdb build                    # migrate and import into tmp/corpusdb/bookstacks.sqlite
py -m corpusdb report                   # all reports; or name some: validation releasable no-pdf ...
py -m corpusdb snapshot                 # deterministic JSON Lines in tmp/corpusdb/snapshot/
py -m corpusdb release <edition> <label>  # try to release an edition's current revision
py -m unittest discover -s corpusdb/tests -t .
```

A full import of the 257 editions takes about 13 seconds and produces a 1.6 MB database. Re-running `build` is incremental: unchanged files keep their revision.

## Layout

| Path | Contents |
| --- | --- |
| `schema/0001_catalogue.sql` | Tables, constraints, triggers and views. Migrations are numbered and applied once. |
| `db.py` | Connections with foreign keys switched on and verified; transactions; migrations. |
| `importer.py` | Read-only import from TEI headers, `author-profiles.json`, `library.ts`, `i18n.ts`, `chinese-sources.json`, `tei_build_config.json`, PDF manifests and the release index. |
| `profile.py` | Bookstacks encoding profile 0.1.0: feature inventory and validation rules. |
| `reports.py` | Report queries and the text snapshot. |
| `tests/` | Constraint, import, profile, assessment and release-gate tests using real fixture editions. |

## Records

| Record | Holds | Points into TEI by |
| --- | --- | --- |
| `language` | Edition languages, read from `EDITION_LANGUAGES` and checked against `LANGUAGE_DATA` | — |
| `contributor`, `work`, `edition` | Preferred author form and portrait; work identity and title (catalogue or slug fallback); edition language, file and public route | file path, root `xml:id` |
| `edition_revision` | One row per distinct TEI content state | SHA-256 of the file |
| `contribution` | Every `titleStmt` name as recorded, with its role | revision |
| `source`, `source_use` | Source URLs, revisions and hashes; build-config inputs; header citations | edition (and section key where the register gives one) |
| `feature_observation` | Automated counts of what a revision encodes | revision |
| `feature_assessment` | Human, LLM or automated judgments of source presence, treatment and review | revision |
| `validation_rule`, `validation_result`, `validation_finding` | Profile rules by version; per-revision outcomes; located findings | revision, nearest `xml:id` |
| `release`, `artifact` | Frozen revisions; PDF copies by location with hash and (when known) source revision | revision |

## Enforcement map

| Requirement | Mechanism | Test |
| --- | --- | --- |
| Foreign keys hold | `PRAGMA foreign_keys = ON` set and verified on every connection | `test_foreign_keys_are_enforced_on_every_connection` |
| Controlled states and identifiers | `CHECK` constraints on `STRICT` tables | `test_enumerations_and_identifiers_are_checked`, `test_unknown_states_are_rejected` |
| One current TEI state per edition | Partial unique index | `test_one_current_revision_per_edition` |
| Changed text does not inherit judgments | Assessments and results attach to a revision; `current_assessment` / `stale_assessment` views | `test_changed_tei_supersedes_revision_and_stales_assessments` |
| An LLM cannot record human review | `CHECK (review <> 'human-reviewed' OR assessor_kind = 'human')` | `test_only_a_person_can_record_human_review` |
| Exclusions are justified | `CHECK` requiring a rationale | `test_exclusion_requires_rationale` |
| "Preserved" needs an assessed source | `CHECK` requiring `source_presence = 'present'` | `test_preserved_requires_assessed_source` |
| No release without current validation | Trigger: results for every rule of the release's profile version | `test_unvalidated_or_other_profile_revision_is_blocked` |
| No release with error findings | Trigger on error-severity results | `test_error_findings_block_release` |
| Releases and released revisions are immutable | `BEFORE UPDATE/DELETE` triggers | `test_clean_revision_can_be_released_once_and_is_immutable` |
| Imports are atomic | One `BEGIN IMMEDIATE` transaction per import; a failure rolls back | observed when a malformed build-config entry stopped the first import |
| Reviewable diffs | Snapshot with natural keys, sorted, no row IDs or timestamps | `test_snapshot_is_deterministic` |

## Profile 0.1.0 results on the full corpus

| Rule | Severity | Editions | Findings |
| --- | --- | --- | --- |
| `pointer-resolves` | error | 15 | 346 |
| `language-tag-allowed` | error | 47 | 629 |
| `header-required-fields` | error | 3 | 3 (Chinese editions without `idno`) |
| `text-language-matches-edition` | error | 1 | 1 (`plato_republic_eng`) |
| `header-source-citation` | warning | 109 | 109 |
| `header-no-empty-elements` | warning | 9 | 968 |
| `header-language-usage` | warning | 6 | 6 |
| `rend-vocabulary` | warning | 12 | 1,113 |
| `q-type-`, `milestone-unit-`, `note-type-vocabulary` | warning | 1 each | 1 each |

194 of 257 current revisions have no error findings and could be released under this profile. Vocabulary drift is a warning because normalizing the TEI versus mapping source values is still an open decision; findings name the profile value each alias maps to.

Other answers the reports give directly: 17 editions have no PDF anywhere (14 Conan Doyle, 3 Chinese); none of the 452 PDF copies (240 committed, 212 release assets) records the TEI revision it came from; 63 work titles come from slugs; 5 authors have several recorded name forms.

## Known gaps

- **Batch source records.** 11 `tei_build_config.json` entries (13 source paths) describe a whole shelf (for example `shakespeare_plays-french`) and the Tolstoy *Novellas* sources state no language, so they cannot be attributed to individual editions. Per-edition source records need a register like `chinese-sources.json`.
- **Original language.** The catalogue does not record a work's original language, so the translator-credit report cannot tell originals from translations.
- **Assessments are empty.** Feature observations are automated counts of the TEI; no source-presence or review judgments have been recorded yet.
- **Release assets have no hashes.** The release index records only URLs.
- **Not in scope yet:** ePub, search indexes, backup/restore procedure, multi-editor workflow, and making the database (rather than the side files) the authority for catalogue records. The plan's cutover rules apply before any of those.

## Next decisions

1. Move catalogue authority into the database: which side files (`author-profiles.json`, `WORK_TITLES`, source registers, manifests) become generated from it, and in what order.
2. Whether the site build reads catalogue data from a committed snapshot or from exported JSON, keeping deployment independent of imports.
3. Where the authoritative copy and backups live, given that a binary database is not a reviewable diff; the snapshot is designed to be the committed review form.
4. The editorial decisions listed in the Stage 1 report (Tolstoy notes, vocabulary normalization, author name forms, PDF authority).
