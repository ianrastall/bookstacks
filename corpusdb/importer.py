"""Read-only import of TEI editions and side files into the corpus database.

Nothing under tei/, public/ or src/ is written. Each import runs in one
transaction. Re-importing an unchanged file keeps its revision; a changed
file creates a new current revision, leaving assessments and validation
results attached to the old one.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from . import profile
from .db import transaction

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}
FILE_PATTERN = re.compile(r"^([a-z0-9-]+)_([a-z0-9-]+)_([a-z]{3})\.xml$")
SMALL_TITLE_WORDS = {"a", "an", "and", "of", "the", "from"}


@dataclass(frozen=True)
class Paths:
    """Repository inputs. Tests point tei_root at temporary copies."""

    root: Path
    tei_root: Path | None = None

    @property
    def tei(self) -> Path:
        return self.tei_root or self.root / "tei"

    @property
    def library_ts(self) -> Path:
        return self.root / "src" / "lib" / "library.ts"

    @property
    def i18n_ts(self) -> Path:
        return self.root / "src" / "lib" / "i18n.ts"

    @property
    def author_profiles(self) -> Path:
        return self.root / "src" / "data" / "author-profiles.json"

    @property
    def downloads(self) -> Path:
        return self.root / "public" / "downloads"

    @property
    def chinese_sources(self) -> Path:
        return self.root / "tei" / "chinese-sources.json"

    @property
    def build_config(self) -> Path:
        return self.root / "tei" / "tei_build_config.json"

    @property
    def release_index(self) -> Path:
        return self.root / "tmp" / "release-pdfs.json"


@dataclass
class ImportSummary:
    editions: int = 0
    new_revisions: int = 0
    unchanged_revisions: int = 0
    sources: int = 0
    artifacts: int = 0
    unmatched: list[str] = field(default_factory=list)


def git_revision(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def edition_languages(paths: Paths) -> list[tuple[str, str, str, str]]:
    """EDITION_LANGUAGES from src/lib/i18n.ts, checked against LANGUAGE_DATA in library.ts."""
    source = paths.i18n_ts.read_text(encoding="utf-8")
    block = source[source.index("export const EDITION_LANGUAGES"):source.index("] as const", source.index("export const EDITION_LANGUAGES"))]
    languages = re.findall(r"code: '([^']+)', teiCode: '([^']+)', name: '([^']+)', nativeName: '([^']+)'", block)
    library = paths.library_ts.read_text(encoding="utf-8")
    table = library[library.index("const LANGUAGE_DATA"):library.index("};", library.index("const LANGUAGE_DATA"))]
    mapping = dict(re.findall(r"(\w{3}): \{ code: '([^']+)'", table))
    declared = {tei_code: code for code, tei_code, _, _ in languages}
    if not languages or mapping != declared:
        raise ValueError(f"Edition languages disagree: i18n.ts {declared} versus library.ts LANGUAGE_DATA {mapping}")
    return [(code, tei_code, name, native) for code, tei_code, name, native in languages]


def work_titles(paths: Paths) -> dict[str, str]:
    source = paths.library_ts.read_text(encoding="utf-8")
    start = source.index("const WORK_TITLES")
    body = source[start:source.index("};", start)]
    return dict(re.findall(r"^\s+'([^']+)': '((?:[^'\\]|\\.)*)'", body, re.M))


def title_from_slug(slug: str) -> str:
    """Mirror of titleFromSlug in src/lib/library.ts."""
    words = slug.split("-")
    return " ".join(word if index and word in SMALL_TITLE_WORDS else word[:1].upper() + word[1:] for index, word in enumerate(words))


def clean(value: str | None) -> str:
    return " ".join((value or "").split())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_corpus(connection: sqlite3.Connection, paths: Paths, files: list[Path] | None = None) -> ImportSummary:
    summary = ImportSummary()
    revision = git_revision(paths.root)
    titles = work_titles(paths)
    languages = edition_languages(paths)
    by_file_code = {tei_code: code for code, tei_code, _, _ in languages}
    profiles = json.loads(paths.author_profiles.read_text(encoding="utf-8"))
    tei_files = sorted(files) if files is not None else sorted(paths.tei.glob("*/*.xml"))

    with transaction(connection):
        connection.executemany(
            "INSERT INTO language (code, file_code, english_name, native_name) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(code) DO UPDATE SET file_code = excluded.file_code, english_name = excluded.english_name, native_name = excluded.native_name",
            languages,
        )
        for slug, record in sorted(profiles.items()):
            connection.execute(
                "INSERT INTO contributor (slug, preferred_name, dates_text, portrait_file, portrait_description) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(slug) DO UPDATE SET preferred_name = excluded.preferred_name, dates_text = excluded.dates_text, "
                "portrait_file = excluded.portrait_file, portrait_description = excluded.portrait_description",
                (slug, record["name"], record.get("dates"), record.get("portrait"), record.get("portraitDescription")),
            )
        connection.executemany("INSERT OR IGNORE INTO feature (code, description) VALUES (?, ?)", [(code, description) for code, description, _ in profile.FEATURES])
        connection.executemany(
            "INSERT OR IGNORE INTO validation_rule (code, profile_version, severity, description) VALUES (?, ?, ?, ?)",
            [(rule.code, profile.PROFILE_VERSION, rule.severity, rule.description) for rule in profile.RULES],
        )

        for path in tei_files:
            match = FILE_PATTERN.match(path.name)
            if not match:
                raise ValueError(f"Unexpected TEI file name: {path}")
            author_slug, work_slug, file_code = match.groups()
            if file_code not in by_file_code:
                raise ValueError(f"{path.name}: language suffix {file_code!r} is not an edition language")
            if author_slug not in profiles:
                summary.unmatched.append(f"{path.name}: no author profile; not published by the site")
                continue
            language = by_file_code[file_code]
            title = titles.get(work_slug)
            connection.execute(
                "INSERT INTO work (author_slug, slug, title, title_source) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(author_slug, slug) DO UPDATE SET title = excluded.title, title_source = excluded.title_source",
                (author_slug, work_slug, title or title_from_slug(work_slug), "catalogue" if title else "slug-fallback"),
            )
            work_id = connection.execute("SELECT id FROM work WHERE author_slug = ? AND slug = ?", (author_slug, work_slug)).fetchone()[0]
            data = path.read_bytes()
            tree = etree.fromstring(data, etree.XMLParser(huge_tree=True, remove_comments=False))
            key = path.stem
            relative = path.relative_to(paths.root).as_posix() if path.is_relative_to(paths.root) else path.as_posix()
            connection.execute(
                "INSERT INTO edition (key, work_id, language_code, tei_path, root_xml_id, route_path) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET work_id = excluded.work_id, language_code = excluded.language_code, "
                "tei_path = excluded.tei_path, root_xml_id = excluded.root_xml_id, route_path = excluded.route_path",
                (key, work_id, language, relative, tree.get(f"{{{XML_NS}}}id"), f"/{language}/authors/{author_slug}/{work_slug}"),
            )
            summary.editions += 1
            digest = hashlib.sha256(data).hexdigest()
            existing = connection.execute("SELECT id FROM edition_revision WHERE edition_key = ? AND tei_sha256 = ?", (key, digest)).fetchone()
            connection.execute("UPDATE edition_revision SET is_current = 0 WHERE edition_key = ? AND is_current = 1", (key,))
            if existing:
                revision_id = existing[0]
                connection.execute("UPDATE edition_revision SET is_current = 1 WHERE id = ?", (revision_id,))
                summary.unchanged_revisions += 1
                validated = connection.execute(
                    "SELECT 1 FROM validation_result WHERE revision_id = ? AND profile_version = ?", (revision_id, profile.PROFILE_VERSION)
                ).fetchone()
                if not validated:
                    validate_revision(connection, revision_id, tree, language)
            else:
                header_title = tree.xpath("string(tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[@type='main' or not(@type)][1])", namespaces=NS)
                revision_id = connection.execute(
                    "INSERT INTO edition_revision (edition_key, tei_sha256, bytes, header_title, observed_git_revision, is_current) VALUES (?, ?, ?, ?, ?, 1)",
                    (key, digest, len(data), clean(header_title) or None, revision),
                ).lastrowid
                summary.new_revisions += 1
                record_revision(connection, revision_id, tree, author_slug, language)
            summary.sources += record_header_sources(connection, key, tree)

        summary.sources += record_source_registers(connection, paths, summary)
        summary.artifacts += record_artifacts(connection, paths, summary)
    return summary


def record_revision(connection: sqlite3.Connection, revision_id: int, tree: etree._Element, author_slug: str, language: str) -> None:
    """Contributions, feature observations and profile validation for a new TEI revision."""
    title_stmt = tree.find(f"{{{TEI_NS}}}teiHeader/{{{TEI_NS}}}fileDesc/{{{TEI_NS}}}titleStmt")
    ordinal = 0
    for node in title_stmt if title_stmt is not None else []:
        if not isinstance(node.tag, str):
            continue
        name = etree.QName(node).localname
        if name not in {"author", "editor", "respStmt", "principal", "funder", "sponsor"}:
            continue
        responsibility = None
        if name == "respStmt":
            responsibility = clean(" ".join(node.xpath("tei:resp//text()", namespaces=NS)))
            recorded = clean(" ".join(node.xpath("tei:name//text() | tei:persName//text() | tei:orgName//text()", namespaces=NS)))
            lowered = responsibility.lower()
            role = "encoder" if node.get(f"{{{XML_NS}}}id") == "bookstacks-encoding" else "translator" if re.search(r"transl|перев|tradu", lowered) else "editor" if "edit" in lowered else "other"
        else:
            recorded = clean(" ".join(node.itertext()))
            role = {"author": "author", "editor": "translator" if (node.get("role") or "").startswith("transl") else "editor"}.get(name, "other")
            responsibility = None if name in {"author", "editor"} else name
        if not recorded:
            continue
        ordinal += 1
        connection.execute(
            "INSERT INTO contribution (revision_id, contributor_slug, role, name_as_recorded, responsibility_as_recorded, ordinal) VALUES (?, ?, ?, ?, ?, ?)",
            (revision_id, author_slug if role == "author" else None, role, recorded, responsibility, ordinal),
        )
    for code, _, expression in profile.FEATURES:
        connection.execute(
            "INSERT INTO feature_observation (revision_id, feature_code, occurrences) VALUES (?, ?, ?)",
            (revision_id, code, int(tree.xpath(f"count({expression})", namespaces=NS))),
        )
    validate_revision(connection, revision_id, tree, language)


def validate_revision(connection: sqlite3.Connection, revision_id: int, tree: etree._Element, language: str) -> None:
    for rule in profile.RULES:
        findings = rule.check(tree, language)
        connection.execute(
            "INSERT INTO validation_result (revision_id, rule_code, profile_version, finding_count) VALUES (?, ?, ?, ?)",
            (revision_id, rule.code, profile.PROFILE_VERSION, len(findings)),
        )
        connection.executemany(
            "INSERT INTO validation_finding (revision_id, rule_code, profile_version, location, detail) VALUES (?, ?, ?, ?, ?)",
            [(revision_id, rule.code, profile.PROFILE_VERSION, location, detail) for location, detail in findings],
        )


def upsert_source(connection: sqlite3.Connection, kind: str, locator: str, provider: str | None = None, title: str | None = None, revision: str | None = None, content_sha256: str | None = None) -> int:
    row = connection.execute("SELECT id FROM source WHERE kind = ? AND locator = ? AND revision IS ?", (kind, locator, revision)).fetchone()
    if row:
        return row[0]
    return connection.execute(
        "INSERT INTO source (kind, locator, provider, title, revision, content_sha256) VALUES (?, ?, ?, ?, ?, ?)",
        (kind, locator, provider, title, revision, content_sha256),
    ).lastrowid


def record_header_sources(connection: sqlite3.Connection, edition_key: str, tree: etree._Element) -> int:
    """Source URLs and bibliographic descriptions as the TEI sourceDesc records them."""
    count = 0
    source_desc = tree.xpath("tei:teiHeader/tei:fileDesc/tei:sourceDesc", namespaces=NS)
    if not source_desc:
        return 0
    for target in sorted(set(source_desc[0].xpath(".//tei:ref/@target | .//tei:ptr/@target", namespaces=NS))):
        if target.startswith(("http://", "https://")):
            source_id = upsert_source(connection, "url", target)
            count += connection.execute("INSERT OR IGNORE INTO source_use (edition_key, source_id, evidence) VALUES (?, ?, 'tei-header')", (edition_key, source_id)).rowcount
    for bibl in source_desc[0].xpath(".//tei:bibl[not(ancestor::tei:bibl)] | .//tei:biblStruct | .//tei:biblFull", namespaces=NS):
        text = clean(" ".join(bibl.itertext()))
        if text:
            source_id = upsert_source(connection, "description", text)
            count += connection.execute("INSERT OR IGNORE INTO source_use (edition_key, source_id, evidence) VALUES (?, ?, 'tei-header')", (edition_key, source_id)).rowcount
    return count


def record_source_registers(connection: sqlite3.Connection, paths: Paths, summary: ImportSummary) -> int:
    """Machine-readable source registers kept beside the importers."""
    count = 0
    if paths.chinese_sources.exists():
        for entry in json.loads(paths.chinese_sources.read_text(encoding="utf-8")):
            edition = connection.execute(
                "SELECT edition.key FROM edition JOIN work ON work.id = edition.work_id WHERE work.slug = ? AND edition.language_code = 'zh-Hans'",
                (entry["work"],),
            ).fetchone()
            if not edition:
                summary.unmatched.append(f"chinese-sources.json: no edition for work {entry['work']}")
                continue
            source_id = upsert_source(connection, "url", entry["url"], entry.get("provider"), entry.get("title"), str(entry["revision"]) if entry.get("revision") is not None else None, entry.get("content_sha256"))
            count += connection.execute(
                "INSERT OR IGNORE INTO source_use (edition_key, source_id, scope, evidence) VALUES (?, ?, ?, 'source-register')",
                (edition[0], source_id, entry.get("key") or "edition"),
            ).rowcount
    if paths.build_config.exists():
        for entry in json.loads(paths.build_config.read_text(encoding="utf-8")):
            author_slug = entry["author"].lower()
            for item in entry.get("sources", []):
                if "lang" not in item:
                    # Attributing a language-less source to every edition of the work would be a guess.
                    summary.unmatched.append(f"tei_build_config.json: {entry['id']} source {item['path']} states no language")
                    continue
                key = f"{author_slug}_{entry['id']}_{item['lang']}"
                if not connection.execute("SELECT 1 FROM edition WHERE key = ?", (key,)).fetchone():
                    summary.unmatched.append(f"tei_build_config.json: no edition {key}")
                    continue
                source_id = upsert_source(connection, "repository-file", item["path"])
                count += connection.execute(
                    "INSERT OR IGNORE INTO source_use (edition_key, source_id, evidence) VALUES (?, ?, 'build-config')",
                    (key, source_id),
                ).rowcount
    return count


def record_artifacts(connection: sqlite3.Connection, paths: Paths, summary: ImportSummary) -> int:
    """PDFs beside TEI, committed exporter output and indexed release assets."""
    connection.execute("DELETE FROM artifact WHERE release_id IS NULL")
    known = {row[0] for row in connection.execute("SELECT key FROM edition")}
    rows: list[tuple] = []
    for pdf in sorted(paths.tei.glob("*/*.pdf")):
        if pdf.stem in known:
            rows.append((pdf.stem, "repository-beside-tei", pdf.relative_to(paths.root).as_posix(), sha256_file(pdf), pdf.stat().st_size, None, None))
    for manifest_path in sorted(paths.downloads.glob("*/*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        key = Path(manifest.get("source_tei", "")).stem
        if key not in known:
            summary.unmatched.append(f"{manifest_path.relative_to(paths.root).as_posix()}: no edition {key!r}")
            continue
        for item in manifest.get("files", []):
            pdf = manifest_path.parent / item["name"]
            actual = sha256_file(pdf) if pdf.exists() else None
            if actual != item.get("sha256"):
                summary.unmatched.append(f"{pdf.relative_to(paths.root).as_posix()}: missing or hash differs from manifest")
                continue
            rows.append((key, "public-downloads", pdf.relative_to(paths.root).as_posix(), actual, pdf.stat().st_size, manifest.get("generator_fingerprint"), manifest_path.relative_to(paths.root).as_posix()))
    if paths.release_index.exists():
        for name, url in sorted(json.loads(paths.release_index.read_text(encoding="utf-8")).items()):
            key = Path(name).stem
            if key in known:
                rows.append((key, "release-asset", url, None, None, None, None))
    connection.executemany(
        "INSERT INTO artifact (edition_key, kind, location_kind, location, sha256, bytes, generator_fingerprint, manifest_path) VALUES (?, 'pdf', ?, ?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)
