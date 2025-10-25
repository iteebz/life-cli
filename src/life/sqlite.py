import sqlite3
import uuid
from pathlib import Path

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"


def init_db():
    """Initialize SQLite database"""
    LIFE_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute("PRAGMA table_info(tasks)")
    cols = cursor.fetchall()
    has_tasks_table = bool(cols)
    is_old_schema = has_tasks_table and cols[0][1] == "id" and "INT" in cols[0][2].upper()

    if is_old_schema:
        _migrate_to_uuid(conn)
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'task',
                focus BOOLEAN DEFAULT 0,
                due DATE NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed TIMESTAMP NULL,
                target_count INTEGER DEFAULT 5
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id TEXT NOT NULL,
                checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reminder_id) REFERENCES tasks(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                UNIQUE(task_id, tag)
            )
        """)

    conn.commit()
    conn.close()


def _migrate_to_uuid(conn):
    """Migrate existing INTEGER id tasks to TEXT UUIDs"""
    try:
        cursor = conn.execute("SELECT id FROM tasks ORDER BY id")
        id_mapping = {old_id: str(uuid.uuid4()) for (old_id,) in cursor.fetchall()}

        conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
        conn.execute("ALTER TABLE checks RENAME TO checks_old")
        conn.execute("ALTER TABLE task_tags RENAME TO task_tags_old")

        conn.execute("""
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'task',
                focus BOOLEAN DEFAULT 0,
                due DATE NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed TIMESTAMP NULL,
                target_count INTEGER DEFAULT 5
            )
        """)
        conn.execute("""
            CREATE TABLE checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id TEXT NOT NULL,
                checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reminder_id) REFERENCES tasks(id)
            )
        """)
        conn.execute("""
            CREATE TABLE task_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                UNIQUE(task_id, tag)
            )
        """)

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
                "INSERT INTO tasks (id, content, category, focus, due, created, completed, target_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, content, category, focus, due, created, completed, target_count),
            )

        cursor = conn.execute("SELECT id, reminder_id, checked FROM checks_old")
        for _check_id, old_reminder_id, checked in cursor.fetchall():
            new_reminder_id = id_mapping.get(old_reminder_id)
            if new_reminder_id:
                conn.execute(
                    "INSERT INTO checks (reminder_id, checked) VALUES (?, ?)",
                    (new_reminder_id, checked),
                )

        cursor = conn.execute("SELECT id, task_id, tag FROM task_tags_old")
        for _tag_id, old_task_id, tag in cursor.fetchall():
            new_task_id = id_mapping.get(old_task_id)
            if new_task_id:
                conn.execute(
                    "INSERT INTO task_tags (task_id, tag) VALUES (?, ?)", (new_task_id, tag)
                )

        conn.execute("DROP TABLE tasks_old")
        conn.execute("DROP TABLE checks_old")
        conn.execute("DROP TABLE task_tags_old")

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
