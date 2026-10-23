"""Queries over the corpus database and a deterministic text snapshot for review."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

REPORTS: dict[str, tuple[str, str]] = {
    "validation": (
        "Profile findings by rule (current revisions)",
        """SELECT rule.code, rule.severity, count(DISTINCT CASE WHEN result.finding_count > 0 THEN result.revision_id END) AS editions,
                  coalesce(sum(result.finding_count), 0) AS findings
           FROM validation_rule rule
           LEFT JOIN validation_result result ON result.rule_code = rule.code AND result.profile_version = rule.profile_version
             AND result.revision_id IN (SELECT id FROM edition_revision WHERE is_current = 1)
           GROUP BY rule.code, rule.severity ORDER BY rule.severity, rule.code""",
    ),
    "releasable": (
        "Current revisions with no error findings under the profile",
        """SELECT count(*) AS releasable, (SELECT count(*) FROM edition_revision WHERE is_current = 1) AS current_revisions
           FROM edition_revision revision WHERE revision.is_current = 1 AND NOT EXISTS (
             SELECT 1 FROM validation_result result JOIN validation_rule rule
               ON rule.code = result.rule_code AND rule.profile_version = result.profile_version
             WHERE result.revision_id = revision.id AND rule.severity = 'error' AND result.finding_count > 0)""",
    ),
    "no-pdf": (
        "Editions with no PDF in any location",
        """SELECT edition.key FROM edition WHERE NOT EXISTS (SELECT 1 FROM artifact WHERE artifact.edition_key = edition.key AND artifact.kind = 'pdf')
           ORDER BY edition.key""",
    ),
    "pdf-provenance": (
        "PDF copies by location and whether their source TEI revision is recorded",
        """SELECT location_kind, count(*) AS files, sum(source_revision_id IS NOT NULL) AS with_source_revision
           FROM artifact WHERE kind = 'pdf' GROUP BY location_kind ORDER BY location_kind""",
    ),
    "titles": (
        "Works titled from their slug rather than the catalogue",
        """SELECT author_slug, slug, title FROM work WHERE title_source = 'slug-fallback' ORDER BY author_slug, slug""",
    ),
    "author-forms": (
        "Authors whose TEI headers record more than one name form",
        """SELECT contributor.slug, contributor.preferred_name, group_concat(DISTINCT contribution.name_as_recorded) AS recorded_forms
           FROM contribution JOIN contributor ON contributor.slug = contribution.contributor_slug
           JOIN edition_revision revision ON revision.id = contribution.revision_id AND revision.is_current = 1
           WHERE contribution.role = 'author'
           GROUP BY contributor.slug HAVING count(DISTINCT contribution.name_as_recorded) > 1 ORDER BY contributor.slug""",
    ),
    "translator-credit": (
        # The catalogue does not yet record a work's original language, so originals appear here too.
        "Editions of multi-language works whose current header names no translator",
        """SELECT edition.key, edition.language_code FROM edition
           JOIN edition_revision revision ON revision.edition_key = edition.key AND revision.is_current = 1
           WHERE EXISTS (SELECT 1 FROM edition other WHERE other.work_id = edition.work_id AND other.language_code <> edition.language_code)
             AND NOT EXISTS (SELECT 1 FROM contribution WHERE contribution.revision_id = revision.id AND contribution.role = 'translator')
           ORDER BY edition.key""",
    ),
    "sources": (
        "Source records by evidence",
        """SELECT evidence, count(DISTINCT edition_key) AS editions, count(*) AS uses FROM source_use GROUP BY evidence ORDER BY evidence""",
    ),
    "stale-assessments": (
        "Assessments attached to a superseded TEI revision",
        """SELECT edition_key, feature_code, assessor_kind, assessor, assessed_on FROM stale_assessment ORDER BY edition_key, feature_code""",
    ),
}


def run_report(connection: sqlite3.Connection, name: str) -> tuple[str, list[str], list[tuple]]:
    title, query = REPORTS[name]
    cursor = connection.execute(query)
    return title, [column[0] for column in cursor.description], [tuple(row) for row in cursor.fetchall()]


# Natural keys only, so a snapshot diff shows what changed rather than renumbered row IDs.
SNAPSHOT_QUERIES: dict[str, str] = {
    "languages": "SELECT code, file_code, english_name, native_name FROM language ORDER BY code",
    "contributors": "SELECT slug, preferred_name, dates_text, portrait_file, portrait_description FROM contributor ORDER BY slug",
    "works": "SELECT author_slug, slug, title, title_source FROM work ORDER BY author_slug, slug",
    "editions": """SELECT edition.key, work.author_slug, work.slug AS work_slug, edition.language_code, edition.tei_path, edition.root_xml_id, edition.route_path,
                          revision.tei_sha256 AS current_tei_sha256, revision.bytes AS current_bytes, revision.header_title
                   FROM edition JOIN work ON work.id = edition.work_id
                   LEFT JOIN edition_revision revision ON revision.edition_key = edition.key AND revision.is_current = 1 ORDER BY edition.key""",
    "contributions": """SELECT revision.edition_key, contribution.ordinal, contribution.role, contribution.contributor_slug, contribution.name_as_recorded, contribution.responsibility_as_recorded
                        FROM contribution JOIN edition_revision revision ON revision.id = contribution.revision_id AND revision.is_current = 1
                        ORDER BY revision.edition_key, contribution.ordinal""",
    "sources": """SELECT source_use.edition_key, source_use.scope, source_use.evidence, source.kind, source.locator, source.provider, source.title, source.revision, source.content_sha256
                  FROM source_use JOIN source ON source.id = source_use.source_id
                  ORDER BY source_use.edition_key, source_use.evidence, source_use.scope, source.kind, source.locator""",
    "feature_observations": """SELECT revision.edition_key, observation.feature_code, observation.occurrences
                               FROM feature_observation observation JOIN edition_revision revision ON revision.id = observation.revision_id AND revision.is_current = 1
                               WHERE observation.occurrences > 0 ORDER BY revision.edition_key, observation.feature_code""",
    "assessments": """SELECT edition_key, feature_code, scope, source_presence, treatment, review, assessor_kind, assessor, evidence, rationale, assessed_on
                      FROM current_assessment ORDER BY edition_key, feature_code, scope, assessor_kind, assessor""",
    "validation_findings": """SELECT revision.edition_key, finding.profile_version, finding.rule_code, finding.location, finding.detail
                              FROM validation_finding finding JOIN edition_revision revision ON revision.id = finding.revision_id AND revision.is_current = 1
                              ORDER BY revision.edition_key, finding.rule_code, finding.location, finding.detail""",
    "artifacts": """SELECT artifact.edition_key, artifact.kind, artifact.location_kind, artifact.location, artifact.sha256, artifact.bytes,
                           revision.tei_sha256 AS source_tei_sha256, artifact.generator_fingerprint, artifact.manifest_path
                    FROM artifact LEFT JOIN edition_revision revision ON revision.id = artifact.source_revision_id
                    ORDER BY artifact.edition_key, artifact.location_kind, artifact.location""",
    "releases": """SELECT revision.edition_key, revision.tei_sha256, release.profile_version, release.label
                   FROM release JOIN edition_revision revision ON revision.id = release.revision_id ORDER BY revision.edition_key, release.label""",
}


def write_snapshot(connection: sqlite3.Connection, output: Path) -> list[Path]:
    """One JSON Lines file per record type, sorted by natural key, for text diffs and review."""
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, query in SNAPSHOT_QUERIES.items():
        cursor = connection.execute(query)
        columns = [column[0] for column in cursor.description]
        path = output / f"{name}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in cursor:
                handle.write(json.dumps(dict(zip(columns, row)), ensure_ascii=False, sort_keys=False) + "\n")
        written.append(path)
    return written
