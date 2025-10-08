import sqlite3
from datetime import date, timedelta
from pathlib import Path

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"
CONTEXT_PATH = LIFE_DIR / "context.md"


def init_db():
    """Initialize SQLite database"""
    LIFE_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'task',
            focus BOOLEAN DEFAULT 0,
            due DATE NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed TIMESTAMP NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_id INTEGER NOT NULL,
            checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reminder_id) REFERENCES tasks(id)
        )
    """)
    conn.commit()
    conn.close()


def add_task(content, category="task", focus=False, due=None):
    """Add task to database"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tasks (content, category, focus, due) VALUES (?, ?, ?, ?)",
        (content, category, focus, due),
    )
    conn.commit()
    conn.close()


def get_pending_tasks():
    """Get all pending tasks ordered by focus and due date"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT id, content, category, focus, due, created
        FROM tasks
        WHERE completed IS NULL
        ORDER BY focus DESC, due ASC NULLS LAST, created ASC
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
    """Mark task as completed"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE tasks SET completed = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def update_task(task_id, content=None, due=None, focus=None):
    """Update task fields"""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    updates = []
    params = []

    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if due is not None:
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


def toggle_focus(task_id, current_focus):
    """Toggle focus status of task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
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
    if CONTEXT_PATH.exists():
        return CONTEXT_PATH.read_text().strip()
    return "No context set"


def set_context(context):
    """Set current life context"""
    LIFE_DIR.mkdir(exist_ok=True)
    CONTEXT_PATH.write_text(context)


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


def check_reminder(reminder_id):
    """Record a reminder check"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO checks (reminder_id) VALUES (?)", (reminder_id,))
    conn.commit()
    conn.close()
