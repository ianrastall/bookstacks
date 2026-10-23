-- Bookstacks corpus database, migration 0001: catalogue, provenance,
-- assessment, validation and release records.
--
-- TEI XML in tei/ remains the authority for literary text. Every record
-- below points into TEI by edition, file hash (edition_revision) and, where
-- needed, xml:id. During the prototype this database is derived and
-- disposable; see corpusdb/README.md.

CREATE TABLE language (
  code TEXT PRIMARY KEY,                       -- BCP 47, as used in routes and xml:lang
  file_code TEXT NOT NULL UNIQUE,              -- ISO 639-3 suffix used in TEI file names
  english_name TEXT NOT NULL,
  native_name TEXT NOT NULL,
  CHECK (length(file_code) = 3)
) STRICT;

CREATE TABLE contributor (
  slug TEXT PRIMARY KEY,
  preferred_name TEXT NOT NULL CHECK (trim(preferred_name) <> ''),
  dates_text TEXT,
  portrait_file TEXT,
  portrait_description TEXT
) STRICT;

CREATE TABLE work (
  id INTEGER PRIMARY KEY,
  author_slug TEXT NOT NULL REFERENCES contributor(slug),
  slug TEXT NOT NULL CHECK (slug GLOB '[a-z0-9]*' AND slug NOT GLOB '*[^a-z0-9-]*'),
  title TEXT NOT NULL CHECK (trim(title) <> ''),
  title_source TEXT NOT NULL CHECK (title_source IN ('catalogue', 'slug-fallback')),
  UNIQUE (author_slug, slug)
) STRICT;

CREATE TABLE edition (
  key TEXT PRIMARY KEY,                        -- TEI file stem, e.g. austen_emma_eng
  work_id INTEGER NOT NULL REFERENCES work(id),
  language_code TEXT NOT NULL REFERENCES language(code),
  tei_path TEXT NOT NULL UNIQUE,               -- repository-relative
  root_xml_id TEXT,
  route_path TEXT NOT NULL UNIQUE              -- public reading route; must never change silently
) STRICT;

-- One row per distinct TEI content state of an edition. A changed file is a
-- new revision; assessments, validation results and releases attach to a
-- revision, so they cannot silently carry over to changed text.
CREATE TABLE edition_revision (
  id INTEGER PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES edition(key),
  tei_sha256 TEXT NOT NULL CHECK (length(tei_sha256) = 64 AND tei_sha256 NOT GLOB '*[^0-9a-f]*'),
  bytes INTEGER NOT NULL CHECK (bytes > 0),
  header_title TEXT,
  observed_git_revision TEXT NOT NULL,
  is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
  UNIQUE (edition_key, tei_sha256)
) STRICT;
CREATE UNIQUE INDEX one_current_revision ON edition_revision(edition_key) WHERE is_current = 1;

-- Names exactly as each edition's TEI header records them, kept beside the
-- catalogue's preferred form rather than overwriting either.
CREATE TABLE contribution (
  id INTEGER PRIMARY KEY,
  revision_id INTEGER NOT NULL REFERENCES edition_revision(id),
  contributor_slug TEXT REFERENCES contributor(slug),
  role TEXT NOT NULL CHECK (role IN ('author', 'translator', 'editor', 'encoder', 'other')),
  name_as_recorded TEXT NOT NULL CHECK (trim(name_as_recorded) <> ''),
  responsibility_as_recorded TEXT,
  ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
  UNIQUE (revision_id, ordinal)
) STRICT;

CREATE TABLE source (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('url', 'repository-file', 'description')),
  locator TEXT NOT NULL CHECK (trim(locator) <> ''),  -- URL, path, or bibliographic text
  provider TEXT,
  title TEXT,
  revision TEXT,
  content_sha256 TEXT CHECK (content_sha256 IS NULL OR length(content_sha256) = 64),
  UNIQUE (kind, locator, revision)
) STRICT;

CREATE TABLE source_use (
  edition_key TEXT NOT NULL REFERENCES edition(key),
  source_id INTEGER NOT NULL REFERENCES source(id),
  scope TEXT NOT NULL DEFAULT 'edition',               -- 'edition' or a section key
  evidence TEXT NOT NULL CHECK (evidence IN ('source-register', 'build-config', 'tei-header')),
  PRIMARY KEY (edition_key, source_id, scope, evidence)
) STRICT;

-- Features are the assessment inventory from the Stage 1 audit.
CREATE TABLE feature (
  code TEXT PRIMARY KEY,
  description TEXT NOT NULL
) STRICT;

-- Automated facts: what the TEI revision encodes. Absence here never means
-- the feature is absent from the source.
CREATE TABLE feature_observation (
  revision_id INTEGER NOT NULL REFERENCES edition_revision(id),
  feature_code TEXT NOT NULL REFERENCES feature(code),
  occurrences INTEGER NOT NULL CHECK (occurrences >= 0),
  PRIMARY KEY (revision_id, feature_code)
) STRICT;

-- Judgments about source presence, treatment and review, bound to one revision.
CREATE TABLE feature_assessment (
  id INTEGER PRIMARY KEY,
  revision_id INTEGER NOT NULL REFERENCES edition_revision(id),
  feature_code TEXT NOT NULL REFERENCES feature(code),
  scope TEXT NOT NULL DEFAULT 'edition',
  source_presence TEXT NOT NULL CHECK (source_presence IN ('unassessed', 'present', 'absent', 'uncertain')),
  treatment TEXT NOT NULL CHECK (treatment IN ('pending', 'preserved', 'partially-preserved', 'excluded-by-scope', 'not-applicable')),
  review TEXT NOT NULL CHECK (review IN ('unreviewed', 'automated-checks-passed', 'human-reviewed', 'unresolved')),
  assessor_kind TEXT NOT NULL CHECK (assessor_kind IN ('automated', 'llm', 'human')),
  assessor TEXT NOT NULL CHECK (trim(assessor) <> ''),  -- person, or tool/model identity
  evidence TEXT NOT NULL CHECK (trim(evidence) <> ''),
  rationale TEXT,
  assessed_on TEXT NOT NULL CHECK (assessed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  -- An exclusion must say why; only a person can record a human review.
  CHECK (treatment <> 'excluded-by-scope' OR trim(coalesce(rationale, '')) <> ''),
  CHECK (review <> 'human-reviewed' OR assessor_kind = 'human'),
  -- "Preserved" is a claim about the source, so the source must have been assessed.
  CHECK (treatment NOT IN ('preserved', 'partially-preserved') OR source_presence = 'present'),
  UNIQUE (revision_id, feature_code, scope, assessor_kind, assessor)
) STRICT;

-- A rule belongs to one profile version; changing a rule means a new version,
-- so results from an older profile cannot authorize a release.
CREATE TABLE validation_rule (
  code TEXT NOT NULL,
  profile_version TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('error', 'warning')),
  description TEXT NOT NULL,
  PRIMARY KEY (code, profile_version)
) STRICT;

-- One row per rule, profile version and revision: the rule ran against that exact TEI state.
CREATE TABLE validation_result (
  revision_id INTEGER NOT NULL REFERENCES edition_revision(id),
  rule_code TEXT NOT NULL,
  profile_version TEXT NOT NULL,
  finding_count INTEGER NOT NULL CHECK (finding_count >= 0),
  PRIMARY KEY (revision_id, rule_code, profile_version),
  FOREIGN KEY (rule_code, profile_version) REFERENCES validation_rule(code, profile_version)
) STRICT;

CREATE TABLE validation_finding (
  id INTEGER PRIMARY KEY,
  revision_id INTEGER NOT NULL,
  rule_code TEXT NOT NULL,
  profile_version TEXT NOT NULL,
  location TEXT NOT NULL,                     -- xml:id of the nearest identified ancestor, or an XPath
  detail TEXT NOT NULL,
  FOREIGN KEY (revision_id, rule_code, profile_version)
    REFERENCES validation_result(revision_id, rule_code, profile_version)
) STRICT;

-- A release freezes one revision. It is append-only.
CREATE TABLE release (
  id INTEGER PRIMARY KEY,
  revision_id INTEGER NOT NULL REFERENCES edition_revision(id),
  profile_version TEXT NOT NULL,
  label TEXT NOT NULL CHECK (trim(label) <> ''),
  UNIQUE (revision_id, label)
) STRICT;

-- Publication files. source_revision_id is NULL when nothing records which
-- TEI state produced the file (true of every PDF manifest observed so far).
CREATE TABLE artifact (
  id INTEGER PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES edition(key),
  kind TEXT NOT NULL CHECK (kind IN ('pdf', 'epub')),
  location_kind TEXT NOT NULL CHECK (location_kind IN ('repository-beside-tei', 'public-downloads', 'release-asset')),
  location TEXT NOT NULL UNIQUE,
  sha256 TEXT CHECK (sha256 IS NULL OR length(sha256) = 64),
  bytes INTEGER CHECK (bytes IS NULL OR bytes > 0),
  source_revision_id INTEGER REFERENCES edition_revision(id),
  generator_fingerprint TEXT,
  manifest_path TEXT,
  release_id INTEGER REFERENCES release(id),
  CHECK (location_kind = 'release-asset' OR sha256 IS NOT NULL)
) STRICT;

-- Release gate: the revision must have results for every rule of the
-- release's profile version, and no error-severity findings.
CREATE TRIGGER release_requires_complete_validation
BEFORE INSERT ON release
WHEN EXISTS (
  SELECT 1 FROM validation_rule rule
  WHERE rule.profile_version = NEW.profile_version
    AND NOT EXISTS (
      SELECT 1 FROM validation_result result
      WHERE result.revision_id = NEW.revision_id
        AND result.rule_code = rule.code
        AND result.profile_version = rule.profile_version
    )
) OR NOT EXISTS (SELECT 1 FROM validation_rule WHERE profile_version = NEW.profile_version)
BEGIN
  SELECT RAISE(ABORT, 'release blocked: revision has not been validated against this profile version');
END;

CREATE TRIGGER release_requires_no_errors
BEFORE INSERT ON release
WHEN EXISTS (
  SELECT 1 FROM validation_result result
  JOIN validation_rule rule ON rule.code = result.rule_code AND rule.profile_version = result.profile_version
  WHERE result.revision_id = NEW.revision_id
    AND result.profile_version = NEW.profile_version
    AND rule.severity = 'error'
    AND result.finding_count > 0
)
BEGIN
  SELECT RAISE(ABORT, 'release blocked: revision has error-severity validation findings');
END;

CREATE TRIGGER release_is_append_only_update
BEFORE UPDATE ON release
BEGIN
  SELECT RAISE(ABORT, 'releases are immutable');
END;

CREATE TRIGGER release_is_append_only_delete
BEFORE DELETE ON release
BEGIN
  SELECT RAISE(ABORT, 'releases are immutable');
END;

-- Revisions with a release keep their content identity.
CREATE TRIGGER released_revision_is_frozen
BEFORE UPDATE OF edition_key, tei_sha256, bytes ON edition_revision
WHEN EXISTS (SELECT 1 FROM release WHERE revision_id = OLD.id)
BEGIN
  SELECT RAISE(ABORT, 'released revisions are immutable');
END;

-- Assessments that apply to the current TEI state only; older ones are stale.
CREATE VIEW current_assessment AS
SELECT assessment.*, revision.edition_key
FROM feature_assessment assessment
JOIN edition_revision revision ON revision.id = assessment.revision_id
WHERE revision.is_current = 1;

CREATE VIEW stale_assessment AS
SELECT assessment.*, revision.edition_key
FROM feature_assessment assessment
JOIN edition_revision revision ON revision.id = assessment.revision_id
WHERE revision.is_current = 0;
