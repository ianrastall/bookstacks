"""Command line for the corpus database prototype.

    py -m corpusdb build                 # migrate and import into tmp/corpusdb/bookstacks.sqlite
    py -m corpusdb report [name ...]     # print reports
    py -m corpusdb snapshot              # write tmp/corpusdb/snapshot/*.jsonl
    py -m corpusdb release KEY LABEL     # attempt a release of an edition's current revision
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from . import profile
from .db import connect, migrate, transaction
from .importer import Paths, import_corpus
from .reports import REPORTS, run_report, write_snapshot

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "tmp" / "corpusdb" / "bookstacks.sqlite"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="corpusdb", description="Bookstacks corpus database prototype")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"database path (default {DEFAULT_DB.relative_to(ROOT)})")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="apply migrations and import TEI and side files")
    build.add_argument("files", nargs="*", type=Path, help="limit the import to these TEI files")
    report = commands.add_parser("report", help="print catalogue reports")
    report.add_argument("names", nargs="*", metavar="name", help=f"any of: {', '.join(REPORTS)} (default: all)")
    snapshot = commands.add_parser("snapshot", help="write a deterministic JSON Lines snapshot")
    snapshot.add_argument("--output", type=Path, default=ROOT / "tmp" / "corpusdb" / "snapshot")
    release = commands.add_parser("release", help="record a release of an edition's current revision")
    release.add_argument("edition")
    release.add_argument("label")
    args = parser.parse_args(argv)
    if args.command == "report" and (unknown := [name for name in args.names if name not in REPORTS]):
        parser.error(f"unknown report: {', '.join(unknown)}")

    args.db.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(args.db)
    if args.command == "build":
        applied = migrate(connection)
        summary = import_corpus(connection, Paths(ROOT), [path.resolve() for path in args.files] or None)
        print(f"Migrations applied: {', '.join(applied) or 'none'}")
        print(f"Editions {summary.editions}; new revisions {summary.new_revisions}; unchanged {summary.unchanged_revisions}; "
              f"source uses {summary.sources}; artifacts {summary.artifacts}; profile {profile.PROFILE_VERSION}")
        for message in summary.unmatched:
            print(f"  not matched: {message}")
    elif args.command == "report":
        for name in args.names or REPORTS:
            title, columns, rows = run_report(connection, name)
            print(f"\n## {title} ({len(rows)} rows)")
            print("\t".join(columns))
            for row in rows:
                print("\t".join("" if value is None else str(value) for value in row))
    elif args.command == "snapshot":
        for path in write_snapshot(connection, args.output):
            print(path)
    elif args.command == "release":
        row = connection.execute("SELECT id FROM edition_revision WHERE edition_key = ? AND is_current = 1", (args.edition,)).fetchone()
        if not row:
            print(f"No current revision for {args.edition}", file=sys.stderr)
            return 1
        try:
            with transaction(connection):
                connection.execute("INSERT INTO release (revision_id, profile_version, label) VALUES (?, ?, ?)", (row[0], profile.PROFILE_VERSION, args.label))
        except sqlite3.DatabaseError as error:
            print(f"{args.edition}: {error}", file=sys.stderr)
            return 1
        print(f"Released {args.edition} as {args.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
