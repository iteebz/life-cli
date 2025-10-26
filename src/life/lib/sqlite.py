import sqlite3
from contextlib import contextmanager
from pathlib import Path

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"


@contextmanager
def get_db():
    """Context manager for safe database connections with auto-commit/rollback."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize SQLite database"""
    LIFE_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            focus BOOLEAN DEFAULT 0,
            due DATE NULL,
            created INTEGER DEFAULT (CAST(CURRENT_TIMESTAMP AS REAL)),
            completed INTEGER NULL,
            target_count INTEGER DEFAULT 5
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            checked INTEGER DEFAULT (CAST(CURRENT_TIMESTAMP AS REAL)),
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS item_tags (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
            UNIQUE(item_id, tag)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_item_tags_item ON item_tags(item_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_item_tags_tag ON item_tags(tag)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_checks_item ON checks(item_id)")

    conn.commit()
    conn.close()


def execute_sql(query):
    """Execute arbitrary SQL query"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        if query.strip().upper().startswith("SELECT"):
            cursor = conn.execute(query)
            return cursor.fetchall()
        conn.execute(query)
        conn.commit()
        return None
    finally:
        conn.close()
