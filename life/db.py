# life/db.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config

MIGRATIONS_TABLE = "_migrations"


@contextmanager
def get_db(db_path: Path | None = None):
    """Context manager for safe database connections with auto-commit/rollback."""
    db_path = db_path if db_path else config.DB_PATH
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_migrations() -> list[tuple[str, str]]:
    """Load migrations from the migrations/ directory."""
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return []

    migrations = []
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        name = sql_file.stem
        sql_content = sql_file.read_text()
        migrations.append((name, sql_content))
    return migrations


def init(db_path: Path | None = None):
    """Initialize SQLite database and apply migrations."""
    db_path = db_path if db_path else config.DB_PATH
    db_path.parent.mkdir(exist_ok=True)
    with get_db(db_path) as conn:
        create_migrations_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        conn.execute(create_migrations_table_sql)

        applied_migrations = {
            row[0] for row in conn.execute(f"SELECT name FROM {MIGRATIONS_TABLE}").fetchall()
        }

        for name, sql_content in load_migrations():
            if name not in applied_migrations:
                conn.executescript(sql_content)
                conn.execute(f"INSERT INTO {MIGRATIONS_TABLE} (name) VALUES (?)", (name,))
