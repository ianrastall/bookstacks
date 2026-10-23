"""Constraint, import and release-gate tests for the corpus database prototype.

    py -m unittest discover -s corpusdb/tests -t .
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from corpusdb import profile
from corpusdb.db import connect, migrate, transaction
from corpusdb.importer import Paths, import_corpus
from corpusdb.reports import write_snapshot

ROOT = Path(__file__).resolve().parents[2]
# Representative fixtures from the Stage 1 audit: clean drama, a missing header
# identifier, invalid inner language tags, and dangling authority references.
FIXTURES = [
    "shakespeare/shakespeare_hamlet_eng.xml",
    "lu-xun/lu-xun_call-to-arms_zho.xml",
    "aristotle/aristotle_poetics_eng.xml",
    "dostoevsky/dostoevsky_the-double_rus.xml",
]


class CorpusTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="corpusdb-"))
        self.tei = self.directory / "tei"
        for fixture in FIXTURES:
            target = self.tei / fixture
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "tei" / fixture, target)
        self.paths = Paths(ROOT, tei_root=self.tei)
        self.connection = self.open_database("test.sqlite")

    def tearDown(self) -> None:
        for connection in getattr(self, "connections", []):
            connection.close()
        shutil.rmtree(self.directory, ignore_errors=True)

    def open_database(self, name: str) -> sqlite3.Connection:
        connection = connect(self.directory / name)
        self.connections = [*getattr(self, "connections", []), connection]
        migrate(connection)
        import_corpus(connection, self.paths)
        return connection

    def current_revision(self, key: str) -> int:
        return self.connection.execute("SELECT id FROM edition_revision WHERE edition_key = ? AND is_current = 1", (key,)).fetchone()[0]

    def release(self, revision_id: int, label: str = "test", version: str = profile.PROFILE_VERSION) -> None:
        with transaction(self.connection):
            self.connection.execute("INSERT INTO release (revision_id, profile_version, label) VALUES (?, ?, ?)", (revision_id, version, label))

    def assess(self, revision_id: int, **values: str) -> None:
        row = {
            "feature_code": "verse", "source_presence": "present", "treatment": "preserved", "review": "human-reviewed",
            "assessor_kind": "human", "assessor": "Ian", "evidence": "Compared Act 1 with the source", "rationale": None, "assessed_on": "2026-10-23",
        } | values
        with transaction(self.connection):
            self.connection.execute(
                "INSERT INTO feature_assessment (revision_id, feature_code, source_presence, treatment, review, assessor_kind, assessor, evidence, rationale, assessed_on) "
                "VALUES (:revision_id, :feature_code, :source_presence, :treatment, :review, :assessor_kind, :assessor, :evidence, :rationale, :assessed_on)",
                row | {"revision_id": revision_id},
            )


class SchemaTests(CorpusTestCase):
    def test_foreign_keys_are_enforced_on_every_connection(self) -> None:
        self.assertEqual(self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("INSERT INTO edition (key, work_id, language_code, tei_path, route_path) VALUES ('x_y_eng', 9999, 'en', 'x', '/en/x')")

    def test_migrations_apply_once(self) -> None:
        self.assertEqual(migrate(self.connection), [])

    def test_enumerations_and_identifiers_are_checked(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("INSERT INTO work (author_slug, slug, title, title_source) VALUES ('shakespeare', 'Bad Slug', 'T', 'catalogue')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("UPDATE edition_revision SET tei_sha256 = 'not-a-hash'")

    def test_one_current_revision_per_edition(self) -> None:
        revision = self.current_revision("shakespeare_hamlet_eng")
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO edition_revision (edition_key, tei_sha256, bytes, observed_git_revision, is_current) VALUES ('shakespeare_hamlet_eng', ?, 1, 'x', 1)",
                ("0" * 64,),
            )
        self.assertEqual(self.current_revision("shakespeare_hamlet_eng"), revision)


class ImportTests(CorpusTestCase):
    def test_editions_routes_and_contributions(self) -> None:
        row = self.connection.execute("SELECT language_code, route_path, root_xml_id FROM edition WHERE key = 'lu-xun_call-to-arms_zho'").fetchone()
        self.assertEqual(tuple(row), ("zh-Hans", "/zh-Hans/authors/lu-xun/call-to-arms", row["root_xml_id"]))
        authors = self.connection.execute(
            "SELECT contributor_slug FROM contribution JOIN edition_revision r ON r.id = contribution.revision_id WHERE r.edition_key = 'shakespeare_hamlet_eng' AND role = 'author'"
        ).fetchall()
        self.assertEqual([row[0] for row in authors], ["shakespeare"])

    def test_feature_observations_count_encoding(self) -> None:
        speeches = self.connection.execute(
            "SELECT occurrences FROM feature_observation WHERE revision_id = ? AND feature_code = 'dramatic-speech'", (self.current_revision("shakespeare_hamlet_eng"),)
        ).fetchone()[0]
        self.assertGreater(speeches, 1000)

    def test_source_register_entries_attach_to_their_edition(self) -> None:
        count = self.connection.execute(
            "SELECT count(*) FROM source_use WHERE edition_key = 'lu-xun_call-to-arms_zho' AND evidence = 'source-register'"
        ).fetchone()[0]
        self.assertGreater(count, 10)

    def test_unchanged_reimport_keeps_the_revision(self) -> None:
        before = self.current_revision("shakespeare_hamlet_eng")
        summary = import_corpus(self.connection, self.paths)
        self.assertEqual((summary.new_revisions, summary.unchanged_revisions), (0, len(FIXTURES)))
        self.assertEqual(self.current_revision("shakespeare_hamlet_eng"), before)

    def test_changed_tei_supersedes_revision_and_stales_assessments(self) -> None:
        first = self.current_revision("shakespeare_hamlet_eng")
        self.assess(first)
        path = self.tei / "shakespeare/shakespeare_hamlet_eng.xml"
        path.write_bytes(path.read_bytes().replace(b"</TEI>", b"<!-- edited --></TEI>"))
        summary = import_corpus(self.connection, self.paths)
        second = self.current_revision("shakespeare_hamlet_eng")
        self.assertEqual(summary.new_revisions, 1)
        self.assertNotEqual(first, second)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM current_assessment WHERE edition_key = 'shakespeare_hamlet_eng'").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM stale_assessment WHERE edition_key = 'shakespeare_hamlet_eng'").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM validation_result WHERE revision_id = ?", (second,)).fetchone()[0], len(profile.RULES))

    def test_snapshot_is_deterministic(self) -> None:
        other = self.open_database("second.sqlite")
        first_files = write_snapshot(self.connection, self.directory / "a")
        second_files = write_snapshot(other, self.directory / "b")
        for left, right in zip(first_files, second_files):
            self.assertEqual(left.read_bytes(), right.read_bytes(), left.name)


class ProfileTests(CorpusTestCase):
    def findings(self, key: str, rule: str) -> list[str]:
        return [row[0] for row in self.connection.execute(
            "SELECT detail FROM validation_finding WHERE revision_id = ? AND rule_code = ? ORDER BY detail", (self.current_revision(key), rule)
        )]

    def test_dangling_references_are_reported(self) -> None:
        details = self.findings("dostoevsky_the-double_rus", "pointer-resolves")
        self.assertTrue(details)
        self.assertTrue(all("points to undeclared #" in detail for detail in details))

    def test_missing_header_identifier_is_reported(self) -> None:
        self.assertEqual(self.findings("lu-xun_call-to-arms_zho", "header-required-fields"), ["missing publication identifier"])

    def test_invalid_language_tags_are_reported_with_corrections(self) -> None:
        self.assertTrue(self.findings("aristotle_poetics_eng", "language-tag-allowed"))

    def test_clean_edition_has_no_error_findings(self) -> None:
        errors = self.connection.execute(
            "SELECT count(*) FROM validation_result r JOIN validation_rule u ON u.code = r.rule_code AND u.profile_version = r.profile_version "
            "WHERE r.revision_id = ? AND u.severity = 'error' AND r.finding_count > 0",
            (self.current_revision("shakespeare_hamlet_eng"),),
        ).fetchone()[0]
        self.assertEqual(errors, 0)


class AssessmentTests(CorpusTestCase):
    def test_only_a_person_can_record_human_review(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.assess(self.current_revision("shakespeare_hamlet_eng"), assessor_kind="llm", assessor="claude-opus-5-5")

    def test_exclusion_requires_rationale(self) -> None:
        revision = self.current_revision("shakespeare_hamlet_eng")
        with self.assertRaises(sqlite3.IntegrityError):
            self.assess(revision, treatment="excluded-by-scope", review="unreviewed")
        self.assess(revision, treatment="excluded-by-scope", review="unreviewed", rationale="Profile excludes print line numbers")

    def test_preserved_requires_assessed_source(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.assess(self.current_revision("shakespeare_hamlet_eng"), source_presence="unassessed")

    def test_unknown_states_are_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.assess(self.current_revision("shakespeare_hamlet_eng"), review="probably-fine")


class ReleaseTests(CorpusTestCase):
    def test_clean_revision_can_be_released_once_and_is_immutable(self) -> None:
        revision = self.current_revision("shakespeare_hamlet_eng")
        self.release(revision)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("UPDATE release SET label = 'changed'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("DELETE FROM release")
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("UPDATE edition_revision SET bytes = 1 WHERE id = ?", (revision,))

    def test_error_findings_block_release(self) -> None:
        for key in ("dostoevsky_the-double_rus", "lu-xun_call-to-arms_zho", "aristotle_poetics_eng"):
            with self.subTest(key), self.assertRaisesRegex(sqlite3.IntegrityError, "error-severity"):
                self.release(self.current_revision(key))

    def test_unvalidated_or_other_profile_revision_is_blocked(self) -> None:
        revision = self.current_revision("shakespeare_hamlet_eng")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "not been validated"):
            self.release(revision, version="9.9.9")
        with transaction(self.connection):
            self.connection.execute("UPDATE edition_revision SET is_current = 0 WHERE id = ?", (revision,))
            unvalidated = self.connection.execute(
                "INSERT INTO edition_revision (edition_key, tei_sha256, bytes, observed_git_revision, is_current) VALUES ('shakespeare_hamlet_eng', ?, 1, 'x', 1)",
                ("a" * 64,),
            ).lastrowid
        with self.assertRaisesRegex(sqlite3.IntegrityError, "not been validated"):
            self.release(unvalidated)


if __name__ == "__main__":
    unittest.main()
