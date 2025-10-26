import sqlite3
import uuid
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

    cursor = conn.execute("PRAGMA table_info(items)")
    cols = cursor.fetchall()
    has_items_table = bool(cols)

    if not has_items_table:
        cursor = conn.execute("PRAGMA table_info(tasks)")
        cols = cursor.fetchall()
        has_tasks_table = bool(cols)
        is_old_schema = (
            has_tasks_table and len(cols) > 0 and cols[0][1] == "id" and "INT" in cols[0][2].upper()
        )

        if is_old_schema:
            _migrate_to_uuid(conn)
        elif has_tasks_table:
            _migrate_tasks_to_items(conn)
        else:
            _create_schema(conn)

        conn.commit()

    conn.close()


def _create_schema(conn):
    """Create new unified schema"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            focus BOOLEAN DEFAULT 0,
            due DATE NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed TIMESTAMP NULL,
            target_count INTEGER DEFAULT 5
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS item_tags (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id),
            UNIQUE(item_id, tag)
        )
    """)


def _migrate_to_uuid(conn):
    """Migrate existing INTEGER id tasks to TEXT UUIDs"""
    try:
        cursor = conn.execute("SELECT id FROM tasks ORDER BY id")
        id_mapping = {old_id: str(uuid.uuid4()) for (old_id,) in cursor.fetchall()}

        conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
        conn.execute("ALTER TABLE checks RENAME TO checks_old")
        conn.execute("ALTER TABLE task_tags RENAME TO task_tags_old")

        _create_schema(conn)

        cursor = conn.execute(
            "SELECT id, content, category, focus, due, created, completed, target_count FROM tasks_old"
        )
        for (
            old_id,
            content,
            category,
            focus,
            due,
            created,
            completed,
            target_count,
        ) in cursor.fetchall():
            new_id = id_mapping[old_id]
            conn.execute(
                "INSERT INTO items (id, content, focus, due, created, completed, target_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_id, content, focus, due, created, completed, target_count),
            )
            if category in ("habit", "chore"):
                conn.execute(
                    "INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), new_id, category),
                )

        cursor = conn.execute("SELECT id, reminder_id, checked FROM checks_old")
        for _check_id, old_reminder_id, checked in cursor.fetchall():
            new_reminder_id = id_mapping.get(old_reminder_id)
            if new_reminder_id:
                conn.execute(
                    "INSERT INTO checks (id, item_id, checked) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), new_reminder_id, checked),
                )

        cursor = conn.execute("SELECT id, task_id, tag FROM task_tags_old")
        for _tag_id, old_task_id, tag in cursor.fetchall():
            new_task_id = id_mapping.get(old_task_id)
            if new_task_id:
                conn.execute(
                    "INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), new_task_id, tag),
                )

        conn.execute("DROP TABLE tasks_old")
        conn.execute("DROP TABLE checks_old")
        conn.execute("DROP TABLE task_tags_old")

        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _migrate_tasks_to_items(conn):
    """Migrate tasks table to new items/item_tags schema"""
    try:
        conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
        conn.execute("ALTER TABLE task_tags RENAME TO task_tags_old")

        _create_schema(conn)

        cursor = conn.execute(
            "SELECT id, content, category, focus, due, created, completed, target_count FROM tasks_old"
        )
        for (
            task_id,
            content,
            category,
            focus,
            due,
            created,
            completed,
            target_count,
        ) in cursor.fetchall():
            conn.execute(
                "INSERT INTO items (id, content, focus, due, created, completed, target_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, content, focus, due, created, completed, target_count),
            )
            if category in ("habit", "chore"):
                conn.execute(
                    "INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), task_id, category),
                )

        cursor = conn.execute("SELECT id, task_id, tag FROM task_tags_old")
        for _tag_id, task_id, tag in cursor.fetchall():
            conn.execute(
                "INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), task_id, tag),
            )

        conn.execute("DROP TABLE tasks_old")
        conn.execute("DROP TABLE task_tags_old")
        conn.execute("DROP TABLE checks")

        cursor = conn.execute("PRAGMA table_info(checks_old)")
        if cursor.fetchall():
            cursor = conn.execute("SELECT id, reminder_id, checked FROM checks_old")
            for _check_id, reminder_id, checked in cursor.fetchall():
                conn.execute(
                    "INSERT INTO checks (id, item_id, checked) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), reminder_id, checked),
                )
            conn.execute("DROP TABLE checks_old")

        conn.commit()
    except Exception:
        conn.rollback()
        raise


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
