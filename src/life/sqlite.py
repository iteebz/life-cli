import shutil
import sqlite3
import uuid
import yaml
from datetime import date, datetime, timedelta
from pathlib import Path

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"
CONTEXT_MD = LIFE_DIR / "context.md"
PROFILE_MD = LIFE_DIR / "profile.md"
CONFIG_PATH = LIFE_DIR / "config.yaml"
BACKUP_DIR = Path.home() / ".life_backups"


def init_db():
    """Initialize SQLite database"""
    LIFE_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # Check if tasks table exists and has INTEGER id (old schema)
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
        # Create mapping of old int IDs to new UUIDs
        cursor = conn.execute("SELECT id FROM tasks ORDER BY id")
        id_mapping = {old_id: str(uuid.uuid4()) for old_id, in cursor.fetchall()}
        
        # Create new tables with UUID schema
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
        
        # Migrate data
        cursor = conn.execute("SELECT id, content, category, focus, due, created, completed, target_count FROM tasks_old")
        for old_id, content, category, focus, due, created, completed, target_count in cursor.fetchall():
            new_id = id_mapping[old_id]
            conn.execute(
                "INSERT INTO tasks (id, content, category, focus, due, created, completed, target_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, content, category, focus, due, created, completed, target_count)
            )
        
        # Migrate checks
        cursor = conn.execute("SELECT id, reminder_id, checked FROM checks_old")
        for check_id, old_reminder_id, checked in cursor.fetchall():
            new_reminder_id = id_mapping.get(old_reminder_id)
            if new_reminder_id:
                conn.execute(
                    "INSERT INTO checks (reminder_id, checked) VALUES (?, ?)",
                    (new_reminder_id, checked)
                )
        
        # Migrate tags
        cursor = conn.execute("SELECT id, task_id, tag FROM task_tags_old")
        for tag_id, old_task_id, tag in cursor.fetchall():
            new_task_id = id_mapping.get(old_task_id)
            if new_task_id:
                conn.execute(
                    "INSERT INTO task_tags (task_id, tag) VALUES (?, ?)",
                    (new_task_id, tag)
                )
        
        # Drop old tables
        conn.execute("DROP TABLE tasks_old")
        conn.execute("DROP TABLE checks_old")
        conn.execute("DROP TABLE task_tags_old")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise


def add_task(content, category="task", focus=False, due=None, target_count=5):
    """Add task to database"""
    init_db()
    task_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tasks (id, content, category, focus, due, target_count) VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, content, category, focus, due, target_count),
    )
    conn.commit()
    conn.close()
    return task_id


def get_pending_tasks():
    """Get all pending tasks ordered by focus and due date"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT t.id, t.content, t.category, t.focus, t.due, t.created, MAX(c.checked), COUNT(c.id), t.target_count
        FROM tasks t
        LEFT JOIN checks c ON t.id = c.reminder_id
        WHERE t.completed IS NULL
        GROUP BY t.id
        ORDER BY t.focus DESC, t.due ASC NULLS LAST, t.created ASC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def today_completed():
    """Get count of tasks completed and reminders checked today"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today_str = date.today().isoformat()

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE DATE(completed) = ?
    """,
        (today_str,),
    )
    task_count = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM checks
        WHERE DATE(checked) = ?
    """,
        (today_str,),
    )
    check_count = cursor.fetchone()[0]

    conn.close()
    return task_count + check_count


def weekly_momentum():
    """Get weekly completion stats for this week and last week"""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start

    week_start_str = week_start.isoformat()
    last_week_start_str = last_week_start.isoformat()
    last_week_end_str = last_week_end.isoformat()

    # This week completed tasks
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE completed IS NOT NULL
        AND DATE(completed) >= ?
    """,
        (week_start_str,),
    )
    this_week_tasks = cursor.fetchone()[0]

    # This week checked reminders
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM checks
        WHERE DATE(checked) >= ?
    """,
        (week_start_str,),
    )
    this_week_checks = cursor.fetchone()[0]
    this_week_completed = this_week_tasks + this_week_checks

    # This week added
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE DATE(created) >= ?
    """,
        (week_start_str,),
    )
    this_week_added = cursor.fetchone()[0]

    # Last week completed tasks
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE completed IS NOT NULL
        AND DATE(completed) >= ?
        AND DATE(completed) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_tasks = cursor.fetchone()[0]

    # Last week checked reminders
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM checks
        WHERE DATE(checked) >= ?
        AND DATE(checked) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_checks = cursor.fetchone()[0]
    last_week_completed = last_week_tasks + last_week_checks

    # Last week added
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE DATE(created) >= ?
        AND DATE(created) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_added = cursor.fetchone()[0]

    conn.close()
    return this_week_completed, this_week_added, last_week_completed, last_week_added


def complete_task(task_id):
    """Mark task as completed and unfocus"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE tasks SET completed = CURRENT_TIMESTAMP, focus = 0 WHERE id = ?", (task_id,)
    )
    conn.commit()
    conn.close()


def uncomplete_task(task_id):
    """Mark task as incomplete"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE tasks SET completed = NULL WHERE id = ?", (task_id,)
    )
    conn.commit()
    conn.close()


_CLEAR = object()

def update_task(task_id, content=None, due=_CLEAR, focus=None):
    """Update task fields"""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    updates = []
    params = []

    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if due is not _CLEAR:
        updates.append("due = ?")
        params.append(due)
    if focus is not None:
        updates.append("focus = ?")
        params.append(1 if focus else 0)

    if updates:
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        params.append(task_id)
        conn.execute(query, params)
        conn.commit()

    conn.close()


def toggle_focus(task_id, current_focus, category=None):
    """Toggle focus status of task (tasks only)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    if category and category != "task":
        conn.close()
        return current_focus
    new_focus = 1 if current_focus == 0 else 0
    conn.execute("UPDATE tasks SET focus = ? WHERE id = ?", (new_focus, task_id))
    conn.commit()
    conn.close()
    return new_focus


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


def get_context():
    """Get current life context"""
    if CONTEXT_MD.exists():
        return CONTEXT_MD.read_text().strip()
    return "No context set"


def set_context(context):
    """Set current life context"""
    LIFE_DIR.mkdir(exist_ok=True)
    CONTEXT_MD.write_text(context)


def clear_all_tasks():
    """Delete all tasks"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Delete a task from the database"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def check_reminder(reminder_id, check_date=None):
    """Record a reminder check, one per day max. Skip if already checked today. Auto-remove if target reached."""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    if not check_date:
        check_date = date.today().isoformat()

    cursor = conn.execute(
        "SELECT id FROM checks WHERE reminder_id = ? AND DATE(checked) = ?",
        (reminder_id, check_date),
    )
    if cursor.fetchone():
        conn.close()
        return

    conn.execute(
        "INSERT INTO checks (reminder_id, checked) VALUES (?, ?)", (reminder_id, check_date)
    )

    cursor = conn.execute("SELECT target_count FROM tasks WHERE id = ?", (reminder_id,))
    target = cursor.fetchone()

    if target:
        cursor = conn.execute("SELECT COUNT(*) FROM checks WHERE reminder_id = ?", (reminder_id,))
        count = cursor.fetchone()[0]
        target_count = target[0]

        if count >= target_count:
            conn.execute("DELETE FROM tasks WHERE id = ?", (reminder_id,))

    conn.commit()
    conn.close()


def get_profile():
    """Get current profile"""
    if PROFILE_MD.exists():
        return PROFILE_MD.read_text().strip()
    return ""


def set_profile(profile):
    """Set current profile"""
    LIFE_DIR.mkdir(exist_ok=True)
    PROFILE_MD.write_text(profile)


def add_tag(task_id, tag):
    """Add a tag to a task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO task_tags (task_id, tag) VALUES (?, ?)",
            (task_id, tag.lower()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_tags(task_id):
    """Get all tags for a task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT tag FROM task_tags WHERE task_id = ?", (task_id,))
    tags = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tags


def get_tasks_by_tag(tag):
    """Get all pending tasks with a specific tag"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """
        SELECT t.id, t.content, t.category, t.focus, t.due, t.created, MAX(c.checked), COUNT(c.id), t.target_count
        FROM tasks t
        LEFT JOIN checks c ON t.id = c.reminder_id
        INNER JOIN task_tags tt ON t.id = tt.task_id
        WHERE t.completed IS NULL AND tt.tag = ?
        GROUP BY t.id
        ORDER BY t.focus DESC, t.due ASC NULLS LAST, t.created ASC
    """,
        (tag.lower(),),
    )
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def remove_tag(task_id, tag):
    """Remove a tag from a task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "DELETE FROM task_tags WHERE task_id = ? AND tag = ?",
        (task_id, tag.lower()),
    )
    conn.commit()
    conn.close()


def get_today_completed():
    """Get all tasks completed today and habit/chore checks today"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today_str = date.today().isoformat()

    cursor = conn.execute(
        """
        SELECT id, content, category, completed
        FROM tasks
        WHERE DATE(completed) = ? AND category = 'task'
        ORDER BY completed DESC
    """,
        (today_str,),
    )
    completed_tasks = cursor.fetchall()

    cursor = conn.execute(
        """
        SELECT t.id, t.content, t.category, c.checked
        FROM tasks t
        INNER JOIN checks c ON t.id = c.reminder_id
        WHERE DATE(c.checked) = ? AND (t.category = 'habit' OR t.category = 'chore')
        ORDER BY c.checked DESC
    """,
        (today_str,),
    )
    checked_items = cursor.fetchall()

    conn.close()
    return completed_tasks + checked_items


def backup():
    """Create timestamped backup of .life/ directory"""
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    shutil.copytree(LIFE_DIR, backup_path, dirs_exist_ok=True)

    return backup_path


def restore(backup_name: str):
    """Restore from a backup"""
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_name}")

    LIFE_DIR.mkdir(exist_ok=True)

    db_file = backup_path / "store.db"
    if db_file.exists():
        shutil.copy2(db_file, DB_PATH)

    ctx_file = backup_path / "context.md"
    if ctx_file.exists():
        shutil.copy2(ctx_file, CONTEXT_MD)

    profile_file = backup_path / "profile.md"
    if profile_file.exists():
        shutil.copy2(profile_file, PROFILE_MD)


def list_backups() -> list[str]:
    """List all available backups"""
    if not BACKUP_DIR.exists():
        return []

    return sorted(
        [d.name for d in BACKUP_DIR.iterdir() if d.is_dir()],
        reverse=True
    )


def get_default_persona() -> str | None:
    """Get default persona from config, or None if not set."""
    if not CONFIG_PATH.exists():
        return None
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
        return config.get("default_persona")
    except Exception:
        return None


def set_default_persona(persona: str) -> None:
    """Set default persona in config."""
    LIFE_DIR.mkdir(exist_ok=True)
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            pass
    config["default_persona"] = persona
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f)
