#!/usr/bin/env python3
"""Repair life-cli SQLite migration history and apply canonical invariants."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "life" / "migrations"
DEFAULT_DB_PATH = Path.home() / ".life" / "store.db"


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table,),
    )
    return cur.fetchone() is not None


def ensure_tables(conn: sqlite3.Connection) -> None:
    if table_exists(conn, "migrations") and not table_exists(conn, "_migrations_old"):
        conn.execute("ALTER TABLE migrations RENAME TO _migrations_old")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # If a fresh `migrations` table was recreated after the rename, drop it to avoid confusion.
    if table_exists(conn, "migrations"):
        conn.execute("DROP TABLE migrations")


def insert_baseline(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "_migrations"):
        raise RuntimeError("_migrations table is missing after setup")

    applied_at = None
    if table_exists(conn, "_migrations_old"):
        cur = conn.execute(
            "SELECT applied_at FROM _migrations_old WHERE name = ?",
            ("001_schema",),
        )
        row = cur.fetchone()
        if row:
            applied_at = row[0]

    if applied_at is not None:
        conn.execute(
            "INSERT OR IGNORE INTO _migrations (name, applied_at) VALUES (?, ?)",
            ("001_foundation", applied_at),
        )
    else:
        conn.execute(
            "INSERT OR IGNORE INTO _migrations (name) VALUES (?)",
            ("001_foundation",),
        )


def apply_canonical(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT 1 FROM _migrations WHERE name = ?", ("002_canonical",))
    if cur.fetchone():
        return

    canonical_sql = (MIGRATIONS_DIR / "002_canonical.sql").read_text()
    conn.executescript(canonical_sql)
    conn.execute("INSERT INTO _migrations (name) VALUES (?)", ("002_canonical",))


def run_verifications(conn: sqlite3.Connection) -> dict[str, int]:
    """Return key invariant counts after migration runs."""
    results: dict[str, int] = {}
    orphan_checks = conn.execute(
        """
        SELECT COUNT(*) FROM checks
        WHERE item_id NOT IN (SELECT id FROM items)
        """
    ).fetchone()[0]
    results["orphan_checks"] = orphan_checks

    orphan_tags = conn.execute(
        """
        SELECT COUNT(*) FROM tags
        WHERE item_id NOT IN (SELECT id FROM items)
        """
    ).fetchone()[0]
    results["orphan_tags"] = orphan_tags

    non_repeat_checks = conn.execute(
        """
        SELECT COUNT(*) FROM checks c
        JOIN items i ON c.item_id = i.id
        WHERE COALESCE(i.is_repeat, 0) = 0
        """
    ).fetchone()[0]
    results["checks_on_non_repeat"] = non_repeat_checks

    return results


def repair(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        ensure_tables(conn)
        insert_baseline(conn)
        apply_canonical(conn)
        conn.commit()

        return run_verifications(conn)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "db_path",
        nargs="?",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to life-cli SQLite database (default: {DEFAULT_DB_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = repair(args.db_path.expanduser())
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
