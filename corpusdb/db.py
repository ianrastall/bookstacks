"""Connections and migrations for the corpus database."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"


def connect(path: Path | str) -> sqlite3.Connection:
    """Open a connection with foreign keys enforced; SQLite leaves them off per connection by default."""
    connection = sqlite3.connect(str(path), isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("SQLite foreign key enforcement could not be enabled")
    return connection


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block atomically, so readers never observe a half-written import."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def migrate(connection: sqlite3.Connection) -> list[str]:
    """Apply schema/NNNN_*.sql files in order; returns the names applied now."""
    connection.execute("CREATE TABLE IF NOT EXISTS schema_migration (version INTEGER PRIMARY KEY, name TEXT NOT NULL) STRICT")
    applied = {row["version"] for row in connection.execute("SELECT version FROM schema_migration")}
    newly_applied: list[str] = []
    for path in sorted(SCHEMA_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        version = int(path.name[:4])
        if version in applied:
            continue
        with transaction(connection):
            for statement in split_statements(path.read_text(encoding="utf-8")):
                connection.execute(statement)
            connection.execute("INSERT INTO schema_migration (version, name) VALUES (?, ?)", (version, path.name))
        newly_applied.append(path.name)
    return newly_applied


def split_statements(script: str) -> list[str]:
    """Split a migration into statements, keeping trigger bodies whole."""
    statements: list[str] = []
    buffer = ""
    for line in script.splitlines(keepends=True):
        if line.lstrip().startswith("--") and not buffer.strip():
            continue
        buffer += line
        if sqlite3.complete_statement(buffer):
            statements.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        raise ValueError(f"Incomplete SQL statement at end of migration: {buffer[:80]!r}")
    return statements
